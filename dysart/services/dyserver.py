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

from io import StringIO
import pickle
import socket

from dysart.messages.messages import StatusMessage
from dysart.messages.errors import *
import dysart.project as project
import dysart.services.service as service
from dysart.services.jobscheduler import Job, JobScheduler
from dysart.services.streams import DysDataStream
from dysart.services.database import Database
import toplevel.conf as conf

import aiohttp.web as web

# TEMPORARY
from dysart.equs_std.equs_features import *


class Dyserver(service.Service):

    def __init__(self,
                 hostname=None,
                 port=None,
                 db_host=None,
                 db_port=None,
                 labber_host=None):
        """Start and connect to standard services
        """
        self.db_server = Database('database')
        self.db_server.start()
        self.db_port = db_port if db_port else self.db_server.port

        self.hostname = hostname if hostname else conf.config['server_hostname']
        self.port = port if port else int(conf.config['server_port'])
        self.db_host = db_host if db_host else conf.config['db_host']
        self.labber_host = labber_host if labber_host else conf.config['labber_host']
        self.job_scheduler = JobScheduler()
        self.logfile = os.path.join(
            conf.dys_path,
            conf.config['logfile_name']
        )
        self.stdmsg = DysDataStream()
        self.stdimg = DysDataStream()
        self.stdfit = DysDataStream()

        self.app = web.Application()
        self.setup_routes()
        
    # TODO marked for deletion
    def is_running(self) -> bool:
        return hasattr(self, 'httpd')

    def _start(self) -> None:
        """Connects to services and runs the server continuously"""
        self.db_connect(self.db_host, self.db_port)
        self.labber_connect(self.labber_host)
        self.job_scheduler.start('{}Starting job scheduler...'.format(messages.TAB))
        self.load_project(conf.config['default_proj'])
        web.run_app(self.app, host=self.hostname, port=self.port)

    def _stop(self) -> None:
        """Ends the server process"""
        self.job_scheduler.stop()
        self.db_server.stop()

    def db_connect(self, host_name, host_port) -> None:
        """Sets up database client for python interpreter.
        """
        with StatusMessage('{}connecting to database...'.format(messages.TAB)):
            try:
                self.db_client = me.connect(conf.config['default_db'], host=host_name, port=host_port)
                # Do the following lines do anything? I actually don't know.
                sys.path.pop(0)
                sys.path.insert(0, os.getcwd())
            except Exception as e:  # TODO
                self.db_client = None
                raise ConnectionError

    def labber_connect(self, host_name) -> None:
        """Sets a labber client to the default instrument server.
        """
        with StatusMessage('{}Connecting to instrument server...'.format(messages.TAB)):
            try:
                with LabberContext():
                    labber_client = Labber.connectToServer(host_name)
            # Pokemon exception handling generally frowned upon, but I'm not
            # sure how to catch both a ConnectionError and an SG_Network.Error.
            except ConnectionError as e:
                labber_client = None
                raise ConnectionError
            finally:
                self.labber_client = labber_client

    def job_scheduler_connect(self) -> None:
        self.job_scheduler = jobscheduler.JobScheduler()
        self.job_scheduler.start()

    def load_project(self, project_path: str):
        """Loads a project into memory, erasing a previous project if it
        existed.
        """
        self.project = project.Project(project_path)
    
    async def authorize(self, request):
        """Auth for an incoming HTTP request. In the future this will probably
        do some more elaborate three-way handshake; for now, it simply checks
        the incoming IP address against a whitelist.
        
        Args:
            request: 

        Raises:
            web.HTTPUnauthorized

        """
        if request.remote not in conf.config['whitelist']:
            raise web.HTTPUnauthorized
    
    async def refresh_feature(self, feature, request):
        """
        
        Args:
            feature: the feature to be refreshed

        Todo:
            Schedule causally-independent features to be refreshed
            concurrently. This should just execute them serially.
            At some point in the near future, I'd like to implement
            a nice concurrent graph algorithm that lets the server
            keep multiple refreshes in flight at once.
        """
        scheduled_features = await feature.expired_ancestors()
        print(f"Feature: {feature.id}\n", 
              getattr(feature, "__expiration_hook__"),
              scheduled_features)
        for scheduled_feature in scheduled_features:
            record = CallRecord(
                remote=request.remote,
                feature=scheduled_feature,
                hostname=socket.gethostname()
            )
            await scheduled_feature.exec_feature(record)

    async def feature_method_handler(self, request):
        """
        
        Args:
            request: 

        Returns:

        """
        await self.authorize(request)
        data = await request.json()
        
        # `data` is expected to be of the form,
        # 
        # data = {
        #     'project': proj.name,
        #     'feature': self.feature.name,
        #     'method': self.name,
        #     'args': args,
        #     'kwargs': kwargs
        # }
        #
        # NOTE the 'project' field is ignored for now

        # Rolling my own remote object protocol...
        try:
            feature = self.project.features[data['feature']]
        except KeyError:
            raise web.HTTPNotFound(
                reason=f"Feature {data['feature']} not found"
            )
        
        method = getattr(feature, data['method'], None)
        if not hasattr(method, 'exposed'):
            # This exception will be raised if there is no such method *or* if
            # the method is unexposed.
            raise web.HTTPNotFound(
                reason=f"Feature {data['feature']} has no method {data['method']}"
            )
        
        if hasattr(method, 'is_refresh'):
            await self.refresh_feature(feature, request)
        
        return_value = method(*data['args'], **data['kwargs'])
        return web.Response(body=pickle.dumps(return_value))

    async def test_handler(self, request):
        print('Running test handler!')
        return web.Response(text="hello, world!")
    
    def setup_routes(self):
        self.app.router.add_get('/', self.test_handler)
        self.app.router.add_post('/remote/feature', self.feature_method_handler)

class LabberContext:
    """A context manager to wrap connections to Labber and capture errors
    """

    def __enter__(self):
        sys.stdout = sys.stderr = self.buff = StringIO()

    def __exit__(self, exc_type, exc_value, traceback):
        sys.stdout, sys.stderr = sys.__stdout__, sys.__stderr__  # restore I/O
        if self._error():
            raise ConnectionError

    def _error(self) -> bool:
        """Checks if an error condition is found in temporary I/O buffer"""
        return 'Error' in self.buff.getvalue()
