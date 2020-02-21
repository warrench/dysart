"""
Utilities for the DySART toplevel. Abstracts config file handling.
"""

import io
import os
from collections.abc import MutableMapping
import fileinput
import sys
from typing import IO, Optional
from warnings import warn
import shutil

# a configuration file is necessary because it contains settings information
# that will be needed even when the mongodb database is down, or not yet
# set up.
# we will use this instead of passing around loads of global state or setting
# and getting environment variables.
CONFIG_FN = '.dysart.conf'
DEFAULT_CONFIG_FN = '.default.conf'
DYS_PATH = os.path.abspath(os.path.join(
            __file__, os.path.pardir, os.path.pardir))

config_path = os.path.join(DYS_PATH, CONFIG_FN)
# Try to ensure that there are at least default values at the expected path.
if not os.path.exists(config_path):
    default_path = os.path.join(DYS_PATH, DEFAULT_CONFIG_FN)
    try:
        shutil.copy2(default_path, config_path)
    except Exception as e:  # Maybe shouldn't use Pokemon exception handling
        print(e)
        print("No config file; failed to copy default config file. Exiting dysart.",
              sys.stderr)
        exit(1)


class FileMapping(MutableMapping):
    """Implements a mapping interface over a file.
    (Why isn't this in the standard library? Is it?)
    """

    def __init__(self, path: str, sep: str = '='):
        self.path = path
        self.sep = sep

    def __ensure_exists(self):
        self.open('a').close()

    def get_line_key(self, line: str) -> str:
        """return the key associated with a line of text"""
        line_key, *_ = line.split(self.sep)
        return line_key.strip()

    def open(self, mode: str) -> IO:
        """return an open file descriptor to the config file"""
        return open(self.path, mode)

    def get(self, key: str, default=None) -> Optional[str]:
        """return the value for a key if it is in the file, otherwise return
        the default value."""
        try:
            val = self[key]
        except KeyError:
            val = default
        return val

    def __iter__(self):
        self.__ensure_exists()
        with self.open('r') as f:
            for line in f:
                yield self.get_line_key(line)

    def __getitem__(self, key: str) -> str:
        """read a single value by parameter name from the config file"""
        self.__ensure_exists()
        with self.open('r') as f:
            for line in f:
                line_key, val = line.split(self.sep, maxsplit=1)
                if line_key.strip() == key:
                    return val.strip()
        raise KeyError(key)

    def __len__(self):
        """get the length of the config file"""
        self.__ensure_exists()
        with self.open('r') as f:
            # just count the number of non-whitespace lines
            n = sum(1 for line in f.readlines() if not line.isspace())
        return n

    def __setitem__(self, key: str, val: str) -> None:
        """write a single value by parameter name into the config file"""
        if self.sep in key:
            raise ValueError('{} contains sepatator \'{}\''.format(key, self.sep))
        if self.sep in val:
            raise ValueError('{} contains sepatator \'{}\''.format(val, self.sep))
        if key.strip() != key:
            warn('key \'{}\' contains whitespace and will be stripped'.format(key))
        if val.strip() != val:
            warn('value \'{}\' contains whitespace and will be stripped'.format(key))
        # search for key in file and replace
        self.__ensure_exists()
        with fileinput.input(self.path, inplace=True) as f:
            key_found = False
            for line in f:
                line = line.rstrip()
                try:
                    line_key, old_val = line.split(self.sep, maxsplit=1)
                except ValueError:
                    pass
                if line_key.strip() == key:
                    line = line.replace(old_val, val)
                    key_found = True
                print(line)  # write the (possibly modified) line
        if not key_found:
            with self.open('a') as f:
                f.write(key.strip() + self.sep + val.strip())

    def __delitem__(self, key: str):
        """delete a single item from the config file"""
        if self.sep in key:
            raise ValueError('{} contains sepatator \'{}\''.format(key, self.sep))
        if key.strip() != key:
            warn('key \'{}\' contains whitespace and will be stripped'.format(key))
        # search for key in file and delete line
        self.__ensure_exists()
        with fileinput.input(self.path, inplace=True) as f:
            for line in f:
                line = line.rstrip()
                line_key = self.get_line_key(line)
                if line_key != key:
                    print(line)


config = FileMapping(config_path)
