#! /bin/python

"""
Author: mcncm, 2019
DySART toplevel administration script
"""

import os
import sys
import argparse
from collections import OrderedDict

import toplevel.conf as conf
import toplevel.util as util


def nothing():
    print('dummy command on platform {}'.format(platform.system()))


def run_command(services) -> int:
    # command dispatch table
    d_table = {
        'on': util.start,
        'off': util.stop,
        # 'set': util.set_var,
        'status': util.status,
        'restart': nothing,
        'help': nothing,
        'labber': nothing,
        'log': nothing,
        'clean': nothing,
        'uninstall': nothing,
        # 'proj': nothing,
        'python': util.dypy_session,  # set up services in interactive session
    }
    command_fun = d_table.get(args.command)
    if command_fun:
        command_fun(services.values())
    return 0


if __name__ == '__main__':
    # Import the modules that have package dependencies, and need the
    # environment to be activated.
    from dysart.services.database import Database
    from dysart.services.dyserver import Dyserver

    # Get handles to some services and dispatch a command
    parser = argparse.ArgumentParser()
    parser.add_argument('command',
                        metavar='command',
                        type=str,
                        help='the dys command to run')

    args = parser.parse_args()
    services = {} #OrderedDict([('database', Database())])
                            # ('dyserver', Dyserver())])
    exit_code = run_command(services)
    exit(exit_code)
