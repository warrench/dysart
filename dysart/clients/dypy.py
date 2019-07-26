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

from toplevel.conf import dys_path, config
from dysart.server.server import Dyserver
import dysart.messages.messages as messages

def feature_tree_setup():
    """
    Set up a default feature tree, e.g. specified by a config script
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
    # this is really pretty dangerous!
    global dyserver
    dyserver = Dyserver()
    messages.configure_logging(logfile=dyserver.logfile)  # should all be managed by server
    feature_tree_setup()
