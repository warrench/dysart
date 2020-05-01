"""
Utilities for the DySART toplevel. Abstracts config file handling.
"""

import os
import sys
import shutil

import yaml

# a configuration file is necessary because it contains settings information
# that will be needed even when the mongodb database is down, or not yet
# set up.
# we will use this instead of passing around loads of global state or setting
# and getting environment variables.
CONFIG_FN = 'config.yaml'
DEFAULT_CONFIG_FN = 'default.yaml'
dys_path = os.path.abspath(os.path.join(
            __file__, os.path.pardir, os.path.pardir))

config_path = os.path.join(dys_path, CONFIG_FN)
# Try to ensure that there are at least default values at the expected path.
if not os.path.exists(config_path):
    default_path = os.path.join(dys_path, DEFAULT_CONFIG_FN)
    try:
        shutil.copy2(default_path, config_path)
    except Exception as e:  # Maybe shouldn't use Pokemon exception handling
        print(e)
        print("No config file; failed to copy default config file. Exiting dysart.",
              sys.stderr)
        exit(1)

with open(config_path, 'r') as f:
    config = yaml.load(f, yaml.Loader)
