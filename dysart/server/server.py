 # -* coding: utf-8 -*-

"""
Author: mcncm 2019

DySART job server

currently using http library; this should not be used in production, as it's
not really a secure solution with sensible defaults. Should migrate to Apache
or Nginx as soon as I understand what I really want.

Why am I doing this?
* Allows multiple clients to request jobs
* Allows new _kinds_ of clients, like "cron" services and web clients (which
  Simon is now asking about)
* Keeps coupling weakish between user and database; probably a good strategy.

TODO
* loggin'
* login
* when the scheduler is shut down, it should die gracefully: preferably dump its
  job queue to a backup file on the database, and recover from this on startup.

Still-open question: how is the request formulated? I imagine that it's basically
python code that the server evaluates. But this is literally the most insecure
thing you can do. So, it needs to be a very restricted subset. Ideally, it would
be sort of good if you're only allowed to call methods on features and have some
value returned.
"""

import os
import sys
import json
from collections import namedtuple
from enum import Enum
import logging
from threading import Thread
from queue import PriorityQueue, Queue
from http import HTTPStatus
import http.server
import socketserver
from urllib.parse import urlparse, parse_qs
from typing import Optional, Union

import mongoengine as me

import Labber
from dysart.messages.messages import cprint

# TEMPORARY
from dysart.equs_std.equs_features import *

# container for structured requests. Develop this as you discover needs.
Request = namedtuple('Request', ['doc_class', 'name', 'method'])

# constants
status_col = int(os.environ['STATUS_COL'])
DEFAULT_DB_PORT = 27017
DEFAULT_LABBER_HOST = 'localhost'
DEFAULT_DB_HOST = 'localhost'

class Dyserver():


    def __init__(self,
                 db_host_name=DEFAULT_DB_HOST,
                 labber_host_name=DEFAULT_LABBER_HOST,
                 db_host_port=DEFAULT_DB_PORT,
                 project=None):
        """
        connect to standard services
        """
        self.db_connect(db_host_name, db_host_port)
        self.labber_connect(labber_host_name)
        self.load_project(project)
        # all hard-coded constants for now. This will/must change!
        self.logfile = os.path.join(os.environ['DYS_PATH'], 'debug_data',
                                   'log', 'dysart.log')

    def db_connect(self, host_name, host_port):
        """
        Set up database client for python interpreter.
        """
        if os.environ['DB_STATUS'] != 'db_off':
            # Check whether the database server is running.
            try:
                cprint('connecting to database server...'.ljust(status_col), end='')
                # Open a connection to the Mongo database
                mongo_client = me.connect('debug_data', host=host_name, port=host_port)
                """ Do the following lines do anything? I actually don't know. """
                sys.path.pop(0)
                sys.path.insert(0, os.getcwd())
                cprint('done.', status='ok')
            except Exception as e:
                # TODO: replace this with a less general exception.
                cprint('failed.', status='fail')
                mongo_client = None
        else:
            cprint('database server is off.', status='warn')
            mongo_client = None
        self.mongo_client = mongo_client

    def labber_connect(self, host_name):
        """
        sets a labber client to the default instrument server.
        """
        try:
            cprint('connecting to instrument server...'.ljust(status_col), end='')
            labber_client = Labber.connectToServer(host_name)
            cprint('done.', status='ok')
        except Exception as e:
            # TODO: replace this with a less general exception.
            print(e)
            cprint('failed.', status='fail')
            labber_client = None
        finally:
            self.labber_client = labber_client

    def load_project(self, proj_name):
        """
        loads a project into memory.
        """
        return
        """
        if not proj_name:
            self.proj_name = None
        else:
            # load each object in a project in this database

            self.proj_name = proj_name
        """

    def set_project(self, proj_name):
        """
        sets the working project
        """


class Status(Enum):
    """
    a simple enum type to make certain success and failure conditions more
    explicit
    """
    OK = 0
    FAIL = 1

    def __bool__(self):
        return self == self.OK


class DysHandler(http.server.BaseHTTPRequestHandler):
    """
    handles requests to DySART system job scheduler

    Structure of queries:
    GET /db_name?user=username&secret=passphrase&request=code
    """

    # all hard-coded for now
    hosts = ['127.0.0.1']
    users = {'root':'root', 'a':'123'}

    qs_tokens = {'user':'user', 'secret':'secret',
                 'class':'class', 'feature':'feature', 'method':'method'}

    def _set_headers_ok(self):
        """set the headers for a good connection"""
        self.send_response(HTTPStatus.OK)
        self.send_header('Content-type', 'text/json')
        self.end_headers()

    def _set_headers_nauth(self):
        """set the headers for a failed authentication"""
        print('unauthorized access')
        self.send_response(HTTPStatus.UNAUTHORIZED)
        self.end_headers()

    def _set_headers_notfound(self):
        """set the headers for a failed authentication"""
        print('requested resource not found')
        self.send_response(HTTPStatus.NOTFOUND)
        self.end_headers()

    def _check_host(self, user):
        """dummy method for checking that a host is on the whitelist"""
        if host in self.hosts:
            return Status.OK
        else:
            return Status.FAIL

    def _check_credentials(self, user, secret):
        """dummy method for user verification"""
        if user and self.users.get(user) == secret:
            return Status.OK
        else:
            return Status.FAIL

    def get_credentials(self) -> (str, str):
        """dummy method to get user creds in request"""
        query = parse_qs(urlparse(self.path).query)
        users = query.get(self.qs_tokens['user'])
        secrets = query.get(self.qs_tokens['secret'])
        return (users[-1] if users else None, secrets[-1] if secrets else None)

    def get_request(self) -> str:
        """dummy method to extract request from query string"""
        # TODO
        query = parse_qs(urlparse(self.path).query)
        query_last = {field: (query.get(field)[-1] if field in query else None)
                   for field in Request._fields}
        request = Request(**query_last)
        return request

    def get_document_class(self, doc_class: str):
        """dummy method for retrieving a Document class from its name
        assumes that this class is in the global namespace
        this is a total hack for right now"""
        return globals()[doc_class]
        #return getattr(sys.modules[__name__], doc_class)

    def handle_request(self, db, request):
        """dummy method for interpreting and fulfilling the request"""
        try:
            feature_class = self.get_document_class(request.doc_class)
            doc = feature_class.objects.get(name=request.name)
            method = getattr(doc, request.method)
            res = method()
        except me.DoesNotExist:
            raise me.DoesNotExist  # to give some kind of error status code
        except me.MultipleObjectsReturned:  # some other error status code
            # Don't do anything yet; just propagate the exception
            raise me.MultipleObjectsReturned
        payload = json.dumps({'res': res})
        return payload

    def do_GET(self):
        print("got a {} from client {}:\n{}\n".format(self.command, self.client_address, self.requestline))
        print("requested path is: {}".format(self.path))
        if self.client_address not in self.hosts:
            self.log_error('received remote connection from {}'.format(self.client_address))
            Exception('bad client address: {}'.format(self.client_address))

        (user, secret) = self.get_credentials()
        if self._check_credentials(user, secret) == Status.FAIL:
            print('bad request: user \'{}\', cred \'{}\''.format(user, secret))
            self._set_headers_nauth()
            return

        print('authenticated user \'{}\''.format(user))

        # tell them the path they requested
        try:
            db = ''
            # request = Request(doc_class='QubitRabi', name='qb_rabi', method='__str__')
            request = self.get_request()
            print(request)
            payload = self.handle_request(db, request)
            response = payload.encode('utf-8')

            self._set_headers_ok()
            self.wfile.write(response)
        except me.DoesNotExist:
            self._set_headers_notfound()
        except me.MultipleObjectsReturned:
            pass


class Job:
    """
    a job to be run by the scheduler
    """

    def __init__(self, calllback):
        self.callback = callback

    def run(self):
        self.callback()


class Scheduler(Queue):
    """
    an instance of the Scheduler class handles job assignment and dispatch
    """

    def get(block=True, timeout=None):
        new_job = super().get(block=block, timeout=timeout)
        new_job.run()


if __name__ == '__main__':
    Context.db_client = db_connect('localhost', 27017)
    Context.labber_client = labber_connect('localhost')
    PORT = 8000  # for now, a hardcoded constant
    with socketserver.TCPServer(("", PORT), DysHandler) as httpd:
        print("serving at port", PORT)
        httpd.serve_forever()
