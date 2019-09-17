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

    # ignore all services passed as arguments
    #services = itertools.chain(services, args)
    #prev_off = [service for service in services if not service.is_running()]
    # for service in prev_off:
    #for service in services:
    #    print(type(services))
    #    service.start()

    # run an interpreter subprocess
    dypy_startup_path = os.path.join(conf.dys_path, 'dypy.py')
    subprocess.run('python -i {}'.format(dypy_startup_path).split())

    #for service in prev_off:
    #    service.stop()


def restart(*services):
    """Stops and starts all services passed as arguments"""
    stop(*services)
    start(*services)
