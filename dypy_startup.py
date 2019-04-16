"""
This module handles startup busywork for the python interpreter,
in particular configuring connection to other system components.

For the time being, these will receive default configurations (i.e. default
databaes and Labber instrument servers). In a future 1.0 release, I would
like for these configurations to respond to user 'project' settings, so that
any given user is automatically connected to a durable instance of their
running physical experiments.
"""

import os
import os.path
import sys
import mongoengine as me
import Labber

# <shame>
"""
The following code block is used to import the Context namespace. Because I
intend this to be called as a PYTHONSTARTUP scrupt, and to be a shared
namespace with other dysart modules, I've done this in a pretty hacky way.
I'm a bit concerend about the fragility of this, so keep an eye on it.

If anyone sees this, let me know if you know a better way to accomplish this.
"""
import importlib.util
context_module_path = os.path.join(
                            os.environ['DYS_PATH'], 'dysart', 'context.py'
                      )
context_spec = importlib.util.spec_from_file_location(
                    'context', context_module_path
               )
context = importlib.util.module_from_spec(context_spec)
context_spec.loader.exec_module(context)
Context = context.Context

"""
The following is the same. I'm sure there's a correct way to do this, but
this is the only way I know right now.
"""
messages_module_path = os.path.join(
                            os.environ['DYS_PATH'], 'dysart', 
                            'measurement', 'messages.py'
                       )
messages_spec = importlib.util.spec_from_file_location(
                    'messages', messages_module_path
                )
messages = importlib.util.module_from_spec(messages_spec)
messages_spec.loader.exec_module(messages)
cprint = messages.cprint
# </shame>

def db_connect(host_name, host_port):
    """
    Set up database client for python interpreter.
    """
    if os.environ['DB_STATUS'] != 'db_off':
        # Check whether the database server is running.
        try:
            cprint('connecting to database server...\t', end='')
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
        cprint(' done.', status='ok')
        return labber_client
    except Exception as e:
        # TODO: replace this with a less general exception.
        cprint(' failed to connect to intrument server.', status='fail')
    return None

if __name__ == '__main__':
    cprint('\nWelcome to DyPy!', status='bold')
    Context.db_client = db_connect('localhost', 27017)
    Context.labber_client = labber_connect('localhost')
    print('')
