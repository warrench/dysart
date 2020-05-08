import os
import itertools
import subprocess

import toplevel.conf as conf


def start(*services):
    """Start all services passed in an iterable or as positional arguments"""
    for service in services:
        service.start()


def stop(*services):
    """Stop all services passed in an iterable or as positional arguments"""
    for service in services:
        service.stop()


def status(*services):
    """Polls all services passed in an iterable or as positional arguments"""
    for service in services:
        service.get_status()


def dypy_session(*args):
    """Launches an interactive Python session with all services running"""

    # run an interpreter subprocess
    dypy_startup_path = os.path.join(conf.dys_path, 'dypy.py')
    subprocess.run('python -i {}'.format(dypy_startup_path).split())


def restart(*services):
    """Stops and starts all services passed as arguments"""
    stop(*services)
    start(*services)

def load_libraries(*libraries):
    """
    Loads a collection of Feature libraries into the global namespace

    Args:
        libraries: A collection of absolute paths to Feature libraries
    """
    for i, library in enumerate(libraries):
        proj_module_path = os.path.join(proj_path)
        proj_spec = importlib.util.spec_from_file_location(
            f'lib{i}', proj_module_path
        )
        proj = importlib.util.module_from_spec(proj_spec)
        proj_spec.loader.exec_module(proj)
