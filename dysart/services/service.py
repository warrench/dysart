import os
import sys
from abc import ABC, abstractmethod
from enum import Enum
import platform
import shutil
import subprocess

from toplevel.conf import dys_path, config
from dysart.messages.errors import AlreadyOnError, AlreadyOffError, ServiceError
from dysart.messages.messages import StatusMessage


class Service(ABC):

    def start(self, message=None):
        if message is None:
            message = 'Starting {}...'.format(self.__class__.__name__)
        with StatusMessage(message):
            if self.is_running():
                raise AlreadyOnError
            self._start()

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


def env_exists(env_manager) -> bool:
    """Checks whether a virtual environment has already been created"""
    if env_manager == 'venv':
        return ENV_NAME in os.listdir(dys_path)
    elif env_manager == 'conda':
        return
    else:
        RuntimeException('unknown environment manager')

def env_create() -> None:
    """Creates a python virtual environment for DySART."""
    env_manager = config.get('env_manager')

    if env_exists(env_manager):
        return  # nothing to do

    with StatusMessage('creating virtual environment...'):
        if env_manager == 'venv':
            subprocess.run(['virtualenv', os.path.join(dys_path, ENV_NAME),
                            '--python=python{}'.format(conf.config[PYTHON_VERSION])])
        elif env_manager == 'conda':
            subprocess.run(['conda', 'create', '-y', '-n', ENV_NAME,
                            'python={}'.format(conf.config[PYTHON_VERSION])])
        else:
            EnvironmentError('unsupported environment manager: {}'.format(env_manager))


def env_status():
    pass


def env_start():
    """Activates the python virtual environment for DySART in a subshell"""

    p = subprocess.Popen('/bin/bash')#, stdin=subprocess.PIPE)
    p.stdin.write(input='cd toplevel && pwd\n'.encode('utf-8'))
    p.stdin = sys.stdin
    """
    env_manager = config.get('env_manager')
    with StatusMessage('activating python environment...'):
        if env_manager == 'venv':
            #exec(open(os.path.join(dys_path, ENV_NAME, 'bin', 'activate_this.py')).read())
            subprocess.run(['source', os.path.join(dys_path, ENV_NAME, 'bin', 'activate')])
        elif env_manager == 'conda':
            subprocess.run(['conda', 'activate', ENV_NAME])
        else:
            EnvironmentError('unsupported environment manager: {}'.format(env_manager))
    """

def env_stop():
    """Deavtivates the python virtual environment for DySART"""
    env_manager = config.get('env_manager')
    with StatusMessage('deavtivating python environment...'):
        if env_manager == 'venv':
            subprocess.run(['deactivate'])
        elif env_manager == 'conda':
            subprocess.run(['conda', 'deactivate'])
        else:
            EnvironmentError('unsupported environment manager: {}'.format(env_manager))


def db_create(db_path: str) -> None:
    pass


def db_status() -> str:
    pass


def db_start():
    pass


def db_stop():
    pass


def start():
    env_start()


def stop():
    env_stop()


def is_running() -> bool:
    pass


def restart():
    if is_running():
        stop()
    start()


def clean_env():
    pass


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

    # create python environment
    create_env()
    activate_env()
    install_requirements()

    # create database
    create_db()


def set_env_manager() -> None:
    """Sets the default environment manager.
    Prioritizes virualenv over Conda."""
    venv_path = shutil.which('virtualenv')
    if venv_path:
        config['env_manager'] = 'venv'
    conda_path = shutil.which('conda')
    if conda_path:
        config['env_manager'] = 'conda'
    else:
        Exception('No environment manager found.')


def install_requirements() -> None:
    """Resolves and installs python dependencies in the virtual environment."""


def set_project_tree() -> None:
    """configures the default project tree"""
    config['DEFAULT_PROJ'] = args.proj
