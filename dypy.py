"""
This module handles startup busywork for the python interpreter,
in particular configuring connection to other system components.

In this iteration, it both manages the server and acts as a client it, mostly
for development and debugging. In ehe future I anticipate there to be a single
interactive client.

For the time being, these will receive default configurations (i.e. default
databaes and Labber instrument servers). In a future 1.0 release, I would
like for these configurations to respond to user 'project' settings, so that
any given user is automatically connected to a durable instance of their
running physical experiments.
"""

import os
import sys
import builtins
from functools import wraps
import importlib.util

import mongoengine as me
import Labber

from toplevel.conf import dys_path, config
from toplevel.util import start, stop, restart, status
from dysart.feature import CallRecord
from dysart.services.dyserver import Dyserver
from dysart.services.database import Database
import dysart.messages.messages as messages

# Auto-documentation assistance
__HELP_FUNCTIONS = []
def _dypy_help(fn):
    __HELP_FUNCTIONS.append(fn)
    return fn

# DyPy builtins

@_dypy_help
def dypy_help():
    """This help info: print to the terminal the available DyPy builtins. May be
    replaced with `less` in the future, to mirror the behavior of `help()`.
    """
    print('')
    for m in __HELP_FUNCTIONS:
        messages.pprint_func(m.__name__, m.__doc__)

@_dypy_help
def quit():
    """Overloads the builtin quit to close all DySART services first.
    """
    stop(*services)
    builtins.quit()

@_dypy_help
def record(uid_pre: str) -> CallRecord:
    """Returns a record matching a hash prefix.

    Args:
        uid_pre (str): a prefix of a hash value uniquely identifying a record.

    Returns:
        CallRecord: the sought record, if there is a unique match

    Raises:
        MultipleObjectsReturned: raised if the hash prefix is not unique
        DoesNotExist: raised if the hash prefix is not found

    """

    # Normalize the input, even though you nominally only accept `str`
    if type(uid_pre) == bytes:
        uid_pre = uid_pre.decode()

    matches = get_records_by_uid_pre(uid_pre)
    if len(matches) > 1:
        raise MultipleObjectsReturned
    elif not matches:
        raise DoesNotExist
    return matches[0]

@_dypy_help
def feature_tree_setup():
    """Set up a default feature tree, e.g. specified by the DySART config file.
    Retrieves the project specified by config variable `DEFAULT_PROJ`
    """
    try:
        proj_path = config['DEFAULT_PROJ']
    except KeyError:
        return
    try:
        proj_module_path = os.path.join(proj_path)
        proj_spec = importlib.util.spec_from_file_location(
                        'proj', proj_module_path
                    )
        proj = importlib.util.module_from_spec(proj_spec)
        proj_spec.loader.exec_module(proj)
        # Get the feature names from the tree
        feature_names = [name for name in dir(proj)
                            if isinstance(getattr(proj, name), me.Document)]
        # And put them in the global namespace
        globals().update({name: getattr(proj, name) for name in feature_names})

    except Exception as e:
        print(str(e))
        print("could not import feature tree.")

if __name__ == '__main__':
    messages.cprint('Welcome to DyPy!', status='bold')
    messages.cprint('Please run `dypy_help()` to learn about this shell\'s builtins.', status='bold')
    # this is really pretty dangerous!
    services = [Database(), Dyserver()]
    db_server = Database()
    dyserver = Dyserver()
    start(db_server, dyserver)
    messages.configure_logging(logfile=dyserver.logfile)  # should all be managed by server
    feature_tree_setup()
