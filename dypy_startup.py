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
import importlib.util

# <shame>
"""
The following code block is used to import the Context namespace. Because I
intend this to be called as a PYTHONSTARTUP scrupt, and to be a shared
namespace with other dysart modules, I've done this in a pretty hacky way.
I'm a bit concerend about the fragility of this, so keep an eye on it.

If anyone sees this, let me know if you know a better way to accomplish this.
"""
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

"""
Constant definitions
"""
# The number of characters in the left-hand column of status lines
status_col = int(os.environ['STATUS_COL'])

def db_connect(host_name, host_port):
    """
    Set up database client for python interpreter.
    """
    if os.environ['DB_STATUS'] != 'db_off':
        # Check whether the database server is running.
        try:
            cprint('connecting to database server...'.ljust(status_col), end='')
            # Open a connection to the Mongo database
            mongo_client = me.connect('debug_data', host=host_name, port=host_port)
            """ Do the following lines do anything? I actually don't know. """ 
            sys.path.pop(0)
            sys.path.insert(0, os.getcwd())
            cprint('done.', status='ok')
            return mongo_client
        except Exception as e:
            # TODO: replace this with a less general exception.
            cprint('failed.', status='fail')
			
            return None
    else:
        cprint('database server is off.', status='warn')
        return None

def labber_connect(host_name):
    """
    Return a labber client to the default instrument server. 
    """
    try:
        cprint('connecting to instrument server...'.ljust(status_col), end='')
        labber_client = Labber.connectToServer('localhost')
        cprint('done.', status='ok')
        return labber_client
    except Exception as e:
        # TODO: replace this with a less general exception.
        cprint('failed.', status='fail')
    return None

def feature_tree_setup():
    """
    Set up a default feature tree, e.g. specified by a config script
    """
    try:
        tree_path = os.environ['DEFAULT_TREE']
    except KeyError:
        return
    try:
        tree_module_path = os.path.join(tree_path)
        tree_spec = importlib.util.spec_from_file_location(
                        'tree', tree_module_path
                    )
        tree = importlib.util.module_from_spec(tree_spec)
        tree_spec.loader.exec_module(tree)
        # Get the feature names from the tree
        feature_names = [name for name in dir(tree)
                            if isinstance(getattr(tree, name), me.Document)]
        # And put them in the global namespace
        globals().update({name: getattr(tree, name) for name in feature_names})

    except Exception as e:
        print(str(e))
        print("could not import feature tree.")


if __name__ == '__main__':
    cprint('Welcome to DyPy!', status='bold')
    Context.db_client = db_connect('localhost', 27017)
    Context.labber_client = labber_connect('localhost')
    Context.logfile = os.path.join(os.environ['DYS_PATH'], 'debug_data',
                                   'log', 'dysart.log')
    messages.configure_logging(logfile=Context.logfile)
    feature_tree_setup()
