"""
This module handles startup busywork for the python interpreter,
in particular configuring connection to other system components.

In this iteration, it both manages the server and acts as a client to it, mostly
for development and debugging. In ehe future I anticipate there to be a single
interactive client.

For the time being, these will receive default configurations (i.e. default
database and Labber instrument servers). In a future 1.0 release, I would
like for these configurations to respond to user 'project' settings, so that
any given user is automatically connected to a durable instance of their
running physical experiments.
"""

import builtins
from typing import *
import os

import mongoengine as me

from toplevel.conf import config
from toplevel.util import start, stop
from dysart.feature import CallRecord, get_records_by_uid_pre
import dysart.project
from dysart.services.dyserver import Dyserver
import dysart.messages.messages as messages


# Prompt
__WELCOME_MESSAGE = """
Welcome to DyPy!
Please run `dypy_help()` to learn about this shell\'s builtins.
"""

__PROJ = None

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
    stop(dyserver)
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
        raise me.MultipleObjectsReturned
    elif not matches:
        raise me.DoesNotExist
    return matches[0]


@_dypy_help
def set_config_var(name: str, val: Any):
     """Sets a variable in the config file, overwriting it if it already
     exists, and creating it if it does not. Config variables are written in
     all-caps by convention. Like environment variables, these variables are
     all stringly-typed.

     Args:
         name (str): The config variable identifier to write to.
         val (type): The value to write to the variable. Must implement
         `__str__` or `__repr__`.
     """
     config[name] = str(val)


@_dypy_help
def get_config_var(name: str):
    """Retrieves a variable from the config file.

    Args:
        name (str): The config variable identifier to read from.

    Returns:
        The value of the variable specified in `name`.

    Raises:
        KeyError: if the name is not present in the config file.
    """
    return config[name]


@_dypy_help
def get_config_keys():
    """Retrieves the names of the config variables currently set.

    Returns:
        List of the currently-set config variables.
    """
    return list(config.keys())


@_dypy_help
def load_project(project_path: Optional[str] = None):
    """Set up a default feature tree, e.g. specified by the DySART config file.
    Retrieves the project specified by config variable `default_proj`

    Args:
        project_path (str): The path relative to `dys_path` to load. defaults
        to `default_proj`.
    """
    # First, remove the current project from the global namespace
    # TODO rewrite this so that load_project is _atomic_.

    clear_project()

    if project_path is None:
        try:
            # Sanitize paths possibly containing e.g. "~"
            project_path = os.path.expanduser(config['default_proj'])
        except KeyError:
            # TODO use an error function from the messages module
            print("no default project path specified.")
            return

    dyserver.load_project(project_path)
    globals().update(dyserver.project.features)


@_dypy_help
def clear_project():
    """Un-loads the working project from the global namespace.

    Returns: None

    """
    try:
        for name, feature in dyserver.project.features.items():
            del globals()[name]
    except AttributeError:
        # presumably there isn't a project yet--pass silently
        pass


@_dypy_help
def print_feature_dag():
    """Print all the features that are currently included.
    """
    for name, feature in dyserver.project.features.items():
        if not feature.parents:  # i.e. if it's a root
            feature.tree()


if __name__ == '__main__':
    messages.cprint(__WELCOME_MESSAGE, status='bold')

    dyserver = Dyserver()
    start(dyserver)
