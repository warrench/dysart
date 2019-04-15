"""
This module handles startup busywork for the python interpreter,
in particular configuring connection to other system components.

For the time being, these will receive default configurations (i.e. default
databaes and Labber instrument servers). In a future "1.0" release, I would
like for these configurations to respond to user 'project' settings, so that
any given user is automatically connected to a durable instance of their
running physical experiments.
"""

import os
import sys
import mongoengine as me
import Labber

def cprint(s, status='ok', **kwargs):
    """ Write to the terminal with color-coded status """
    class Bcolors:
        """ enum class for colored print """
        HEADER = '\033[95m'
        OKBLUE = '\033[94m'
        OKGREEN = '\033[92m'
        WARNING = '\033[93m'
        FAIL = '\033[91m'
        ENDC = '\033[0m'
        BOLD = '\033[1m'
        UNDERLINE = '\033[4m'

    def write_out(s, color):
        print(color + s + Bcolors.ENDC, **kwargs)

    if status == 'ok':
        write_out(s, Bcolors.OKGREEN)
    elif status == 'bold':
        write_out(s, Bcolors.BOLD)
    elif status == 'warn':
        write_out(s, Bcolors.WARNING)
    elif status == 'fail':
        write_out(s, Bcolors.FAIL)

def db_connect(host_name, host_port):
    """
    Set up database client for python interpreter.
    """
    if os.environ['DB_STATUS'] != 'db_off':
        # Check whether the database server is running.
        try:
            cprint('connecting to database...\t\t\t', end='')
            # Open a connection to the Mongo database
            mongo_client = me.connect('debug_data', host=host_name, port=host_port)
            """ Do the following lines do anything useful? """ 
            sys.path.pop(0)
            sys.path.insert(0, os.getcwd())
            cprint(' done.', status='ok')
            return mongo_client
        except Exception as e:
            # TODO: replace this with a less general exception.
            cprint(' failed to connect to database.', status='fail')
            return None
    else:
        cprint('database server is off.', status='warn')
        return None


def labber_connect(host_name):
    """
    Return a labber client to the default instrument server.
    """
    try:
        cprint('connecting to instrument server... \t', end='')
        labber_client = Labber.connectToServer('localhost')
        cprint(' done.')
        return labber_client
    except Exception as e:
        # TODO: replace this with a less general exception.
        cprint(' failed to connect to intrument server.', status='fail')
    return None

if __name__ == '__main__':
    cprint('\nWelcome to DyPy!', status='bold')
    mongo_client = db_connect('localhost', 27017)
    labber_client = labber_connect('localhost')
