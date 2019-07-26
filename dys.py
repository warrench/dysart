"""
Author: mcncm, 2019
DySART toplevel administration script
"""

import os
import sys
import argparse
from collections import OrderedDict

import toplevel.util as util
from dysart.services.database import Database
from dysart.services.dyserver import Dyserver


def nothing():
    print('dummy command on platform {}'.format(platform.system()))


def run_dypy():
    """Runs the interactive python evironment"""


def run_command() -> int:
    # command dispatch table
    d_table = {
        'on': util.start,
        'off': util.stop,
        'status': util.status,
        'restart': nothing,
        'help': nothing,
        'labber': nothing,
        'log': nothing,
        'clean': nothing,
        'uninstall': nothing,
        'proj': nothing,
        'python': run_dypy
    }
    command_fun = d_table.get(args.command)
    if command_fun:
        command_fun(services)
    return 0


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('command',
                        metavar='command',
                        type=str,
                        help='the dys command to run')

    args = parser.parse_args()
    services = OrderedDict([('database', Database()),
                            ('dyserver', Dyserver())])
    exit_code = run_command()
    exit(exit_code)
