# -*- coding: utf-8 -*-

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
from collections import namedtuple
from enum import Enum
from http import HTTPStatus
import http.server
from io import StringIO
import json
import logging
from queue import PriorityQueue, Queue
import socketserver
from threading import Thread
from typing import Optional, Union, Tuple
from urllib.parse import urlparse, parse_qs

import mongoengine as me
import Labber

import dysart.messages.messages as messages
from dysart.messages.messages import StatusMessage
from dysart.messages.errors import *
import dysart.services.service as service
import toplevel.conf as conf

# TEMPORARY
from dysart.equs_std.equs_features import *

# container for structured requests. Develop this as you discover needs.
Request = namedtuple('Request', ['doc_class', 'name', 'method'])


class Dyserver(service.Service):

    def __init__(self, port=None,
                 db_host=None,
                 db_port=None,
                 labber_host=None,
                 project=None):
        """
        connect to standard services
        """
        self.port = port if port else int(conf.config['SERVER_PORT'])
        self.db_host = db_host if db_host else conf.config['DB_HOST']
        self.db_port = db_port if db_port else int(conf.config['DB_PORT'])
        self.labber_host = labber_host if labber_host else conf.config['LABBER_HOST']
        self.project = project
        # all hard-coded constants for now. This will/must change!
        self.logfile = os.path.join(conf.dys_path, 'debug_data',
                                    'log', 'dysart.log')

    def is_running(self) -> bool:
        return hasattr(self, 'httpd')

    def _start(self) -> None:
        """Connects to services and runs the server continuously"""
        try:
            self.db_connect(self.db_host, self.db_port)
            self.labber_connect(self.labber_host)
            self.load_project(self.project)
        except ConnectionError:
            pass
        #with socketserver.TCPServer(("", self.port), DysHandler) as self.httpd:
        #    self.httpd.serve_forever()

    def _stop(self) -> None:
        """Ends the server process"""
        self.httpd.shutdown()

    def db_connect(self, host_name, host_port) -> None:
        """
        Sets up database client for python interpreter.
        """
        with StatusMessage('{}connecting to database server...'.format(messages.TAB)):
            try:
                mongo_client = me.connect('debug_data', host=host_name, port=host_port)
                # Do the following lines do anything? I actually don't know.
                sys.path.pop(0)
                sys.path.insert(0, os.getcwd())
            except Exception as e:
                mongo_client = None
                raise ConnectionError
            finally:
                self.mongo_client = mongo_client

    def labber_connect(self, host_name) -> None:
        """
        sets a labber client to the default instrument server.
        """
        with StatusMessage('{}connecting to instrument server...'.format(messages.TAB)):
            try:
                with LabberContext():
                    labber_client = Labber.connectToServer(host_name)
            except ConnectionError as e:
                labber_client = None
                raise ConnectionError
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


class LabberContext:
    """A context manager to wrap connections to Labber and capture errors"""

    def __enter__(self):
        sys.stdout = sys.stderr = self.buff = StringIO()

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__  # restore I/O
        if self._error():
            raise ConnectionError

    def _error(self) -> bool:
        """Checks if an error condition is found in temporary I/O buffer"""
        return 'Error' in self.buff.getvalue()


class AuthStatus(Enum):
    FAIL = 0
    OK = 1


class DysHandler(http.server.BaseHTTPRequestHandler):
    """
    handles requests to DySART system job scheduler

    Structure of queries:
    GET /db_name?user=username&secret=passphrase&request=code
    """

    # remote hosts from which incoming connections will be accepted.
    hosts = conf.config.get('REMOTE_HOSTS', '127.0.0.1').split(',')
    # hard-coded for now
    users = {'root': 'root', 'a': '123'}

    # right now, this redundancy is an unnecessarily layer of indirection
    qs_tokens = {'user': 'user', 'secret': 'secret',
                 'class': 'class', 'feature': 'feature', 'method': 'method'}

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
            return AuthStatus.OK
        else:
            return AuthStatus.FAIL

    def _check_credentials(self, user, secret):
        """dummy method for user verification"""
        if user and self.users.get(user) == secret:
            return AuthStatus.OK
        else:
            return AuthStatus.FAIL

    def get_credentials(self) -> Tuple[Optional[str], Optional[str]]:
        """dummy method to get user creds in request"""
        query = parse_qs(urlparse(self.path).query)
        users = query.get(self.qs_tokens['user'])
        secrets = query.get(self.qs_tokens['secret'])
        return (users[-1] if users else None, secrets[-1] if secrets else None)

    def get_request(self) -> Request:
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
        if self._check_credentials(user, secret) == AuthStatus.FAIL:
            print('bad request: user \'{}\', cred \'{}\''.format(user, secret))
            self._set_headers_nauth()
            return

        print('authenticated user \'{}\''.format(user))

        # tell them the path they requested
        try:
            db = ''
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
