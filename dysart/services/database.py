import os
import datetime
import platform
import re
import signal
import subprocess
from typing import Optional
from functools import lru_cache

import toplevel.conf as conf
from dysart.services.service import Service
from dysart.messages.errors import *

import psutil

class Database(Service):
    """This Service class should be used to run the MongoDB database server
    backing DySART."""

    def __init__(self, port=None):
        self.proc_output = None  # what does this do?
        # ensure that necessary database directories exist
        for dir in (os.path.split(self.log_path)[0], self.db_dir):
            if not os.path.exists(dir):
                os.makedirs(dir)

    def is_running(self) -> bool:
        """Returns whether a mongod process is running"""
        return self.__process is not None

    @property
    def __process(self):
        """Optionally returns a psutil process. This implementation is probably
        unnecessarily slow. Could be slightly more sophisticated to improve
        performance, if that matters.
        """
        processes = psutil.process_iter()
        for process in processes:
            if 'mongod' in process.name():  # TODO
                return process
        return None

    @property
    def port(self) -> Optional[int]:
        """Optionally returns a port number of a running process; none if not running.
        """
        # TODO really do clean up this fragile method. Abstract away some of the repetition
        # between platforms; if possible remove the dependency on `netstat`, etc.
        system = platform.system()
        if system in 'Linux, Darwin':
            p = psutil.Process(self.pid)
            return p.connections()[0].laddr.port  # TODO can this fail?
        if system == 'Windows':
            # TODO
            #  * any reasonable error handling at all
            #  * relies on specific output behavior of netstat (which might change)
            #  * possibly works accidentally?
            #  * How does this look for mongodb processes, specifically?
            #  * Why did I do this in this way in the first place? Does psutil not work?
            try:
                netstat_output = subprocess.run(
                    f"netstat -ano".split(),
                    capture_output=True
                )
                splits = (line.split() for line in netstat_output.stdout.decode().splitlines()
                          if line.lstrip().startswith('TCP'))
                # NOTE question: What's the difference between field 1 and field 2 in `line`?
                matching_addrs = [line[1] for line in splits if line[4] == str(self.pid)]
                ports = [int(addr.split(':')[1]) for addr in matching_addrs]
                # Is the first nonzero port the right thing to return here?
                return next(port for port in ports if port != 0)
            except Exception as e:
                # TODO bad: pookemon exception handling
                return None

    # I'd rather use cached_property, but a lot of the lab is still on 3.7.
    @property
    @lru_cache(maxsize=1)
    def pid(self) -> Optional[int]:
        """Returns the process id of the running mongod instance, if there is
        one. This """
        process = self.__process
        if process is not None:
            return process.pid
        else:
            return None

    def _start(self) -> None:
        if platform.system() in ('Darwin', 'Linux'):
            command = f"""mongod --port {conf.config["db_port"]} --fork --quiet
            --logappend --logpath {self.log_path} --dbpath {self.db_dir}
            """.split()
            self.completed_proc = subprocess.run(command, capture_output=True)

        elif platform.system() == 'Windows':
            # On Widows, currently rely on service being started externally.
            # There seem to be conflicting requirements here: the blessed way
            # to run this on NT is as a Windows Service, but this can only be
            # done as Administrator--I'm not sure it's possible to start a
            # Service as a subprocess.
            if self.port == None:
                raise ServiceNotFoundError

    def _stop(self) -> None:
        if platform.system() in ('Darwin', 'Linux'):
            os.kill(self.pid, signal.SIGINT)
        elif platform.system() == 'Windows':
            raise NotImplementedError

    @property
    def db_dir(self) -> str:
        # TODO it might actually be a little confusing that this is a property
        return os.path.join(
            conf.dys_path,
            conf.config['default_db'],
            'db'
        )

    @property
    def log_dir(self) -> str:
        # TODO it might actually be a little confusing that this is a property
        return os.path.join(
            conf.dys_path,
            conf.config['default_db'],
            'log'
        )

    @property
    def log_path(self) -> str:
        """Returns the full path of the current logfile"""
        # TODO it might actually be a little confusing that this is a property
        now = datetime.datetime.now()
        base = 'mongod_{}{}{}.log'.format(now.year, now.month, now.day)
        return os.path.join(self.log_dir, str(now.year),
                            str(now.month), base)
