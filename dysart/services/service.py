from abc import ABC, abstractmethod
import platform
import subprocess

from toplevel.conf import config
from dysart.messages.errors import AlreadyOnError, AlreadyOffError, ServiceError
from dysart.messages.messages import StatusMessage


class Service(ABC):

    def register(self):
        pass

    def start(self, message=None):
        if message is None:
            message = 'Starting {}...'.format(self.__class__.__name__)
        with StatusMessage(message):
            if not self.is_running():
                self._start()
            else:
                raise AlreadyOnError
        # if self.is_running() and not hasattr(self, "background_process'):
        #     raise AlreadyOnError
        # self._start()

    def stop(self, message=None):
        if message is None:
            message = 'Stopping {}...'.format(self.__class__.__name__)
        with StatusMessage(message):
            if not self.is_running():
                raise AlreadyOffError
            self._stop()

    def get_status(self):
        with StatusMessage('{}'.format(self.__class__.__name__),
                           donestr='ON', failstr='OFF'):
            if not self.is_running():
                raise ServiceError  # This is pretty bad. Shouldn't be an error.

    @abstractmethod
    def is_running(self) -> bool:
        """placeholder"""

    @abstractmethod
    def _start(self):
        pass

    @abstractmethod
    def _stop(self):
        pass

    def _check_error(self):
        pass

def db_create(db_path: str) -> None:
    pass


def db_status() -> str:
    pass


def db_start():
    pass


def db_stop():
    pass


def is_running() -> bool:
    pass


def restart():
    if is_running():
        stop()
    start()


def clean_db():
    pass


def clean_log():
    pass


def clean_profile():
    pass


def read_log():
    """display the log contents in user\'s default plaintext viewer"""
    if platform.system() == 'Windows':
        pass
    else:
        subprocess.run(['less', config['LOG_PATH']])


def write_profile():
    """modifies user's dotfiles to alias this script to `dys`"""
    pass


def clean():
    pass


def install() -> None:
    """set up dysart installation"""
    # write dys alias to correct profile dotfile

    # create database
    create_db()

def set_project_tree() -> None:
    """configures the default project tree"""
    config['default_proj'] = args.proj
