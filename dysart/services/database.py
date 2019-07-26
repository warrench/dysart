import os
import sys
import datetime
import platform
import re
import signal
import subprocess
from typing import Optional

import toplevel.conf as conf
from dysart.services.service import Service
from dysart.messages.errors import *


class Database(Service):
    """This Service class should be used to run the MongoDB database server
    backing DySART."""

    def __init__(self, port=None):
        self.proc_output = None
        self.port = port if port else int(conf.config['DB_PORT'])

    def is_running(self) -> bool:
        """Returns whether a mongod process is running"""
        if platform.system() in ('Darwin', 'Linux'):
            return bool(self.get_pid())
        elif platform.system() == 'Windows':
            return False
        else:
            raise UnsupportedPlatformError

    def get_pid(self) -> Optional[int]:
        """Returns the process id of the running mongod instance, if there is
        one"""
        proc_output = subprocess.run('pgrep mongod'.split(),
                        capture_output=True).stdout.decode('utf-8')
        pids = [int(x) for x in proc_output.splitlines()
                if x.isnumeric()]  # no pids returns '\n'
        if len(pids) == 0:
            return None
        elif len(pids) == 1:
            return pids[0]
        else:
            raise MultipleInstancesError

    def _start(self):
        head, _ = os.path.split(self.log_path)

        try:  # make the logfile path if it doesn't exist.
            os.makedirs(head)
        except FileExistsError:
            pass

        if platform.system() in ('Darwin', 'Linux'):
            self.completed_proc = subprocess.run(
              'mongod --fork --quiet --logappend --logpath {} --dbpath {}'.format(
                self.log_path, self.db_path).split(), capture_output=True)
            self._check_error()

        elif platform.system() == 'Windows':
            # flags = {}  # put here
            pass

    def _stop(self):
        if platform.system() in ('Darwin', 'Linux'):
            try:
                os.kill(self.get_pid(), signal.SIGINT)
            except Exception:
                pass
        elif platform.system() == 'Windows':
            pass

    @property
    def db_path(self) -> str:
        return conf.config['DB_PATH']

    @property
    def log_path(self) -> str:
        """Returns the full path of the current logfile"""
        now = datetime.datetime.now()
        base = 'mongod_{}{}{}.log'.format(now.year, now.month, now.day)
        return os.path.join(conf.config['LOG_PATH'], str(now.year),
                            str(now.month), base)
