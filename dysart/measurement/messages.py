"""
Standard output messages for displaying hierarchically-organized data such as
recursively-called status lines.
"""

import os
import datetime as dt
from functools import wraps

default_logfile_path = os.path.join(os.environ['DYS_PATH'], 'debug_data',
                                    'log', 'dysart.log')


class Bcolor:
    """
    Enum class for colored printing
    """
    HEADER = '\033[95m'
    OKBLUE = '\033[94m'
    OKGREEN = '\033[92m'
    WARNING = '\033[93m'
    FAIL = '\033[91m'
    ENDC = '\033[0m'
    BOLD = '\033[1m'
    ITALIC = '\033[3m'
    UNDERLINE = '\033[4m'


def cstr(s, status='normal'):
    """
    Wrap a string with ANSI color annotations
    """
    if status == 'ok':
        return Bcolor.OKGREEN + s + Bcolor.ENDC
    elif status == 'fail':
        return Bcolor.FAIL + s + Bcolor.ENDC
    elif status == 'warn':
        return Bcolor.WARNING + s + Bcolor.ENDC
    elif status == 'bold':
        return Bcolor.BOLD + s + Bcolor.ENDC
    elif status == 'italic':
        return Bcolor.ITALIC + s + Bcolor.ENDC
    elif status == 'underline':
        return Bcolor.UNDERLINE + s + Bcolor.ENDC
    else:
        return s

def cprint(s, status='normal', **kwargs):
    """
    Print a string with ANSI color annotations
    """
    print(cstr(s, status), **kwargs)

def msg1(message, level=0, end="\n"):
    """
    Print a formatted message to stdout.
    Accepts an optional level parameter, which is useful when you might wish
    to log a stack trace.
    """
    prompt = '=> '
    indent = '   '
    output = level * indent + prompt + message
    print(output, end=end)


def msg2(message, level=0, end="\n"):
    """
    Print a formatted message to stdout.
    Accepts an optional level parameter, which is useful when you might wish
    to log a stack trace.
    """
    prompt = '-> '
    indent = '   '
    output = level * indent + prompt + message
    print(output, end=end)


def write_log(message, logfile):
    """
    Write a message to a log file with date and time information.
    """
    # TODO: use python standard library logging API to log message "correctly"
    separator = ' | '
    prefix = dt.datetime.now().ctime() + separator
    with open(logfile, 'a') as f:
        f.write(prefix + message + '\n')


def logged(logfile=default_logfile_path, stdout=True,
           message='log event', **kwargs):
    """
    Decorator for handling log messages. By default, writes to a default log
    file in the debug_data database directory, and prints output to stdout.
    Passes level parameter in decorated function to message functions to
    """
    if logfile is None or logfile is '':
        # Set the log output to the null file. This should actually be cross-
        # platform, i.e. equal to '/dev/null' on unix systems and 'NULL' on
        # windows.
        logfile = os.devnull

    # set string terminator for log message
    term = "\n"
    if 'end' in kwargs:
        term = kwargs['end']

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs_inner):
            # write stdout message
            if stdout:
                if 'level' in kwargs_inner:
                    lvl = kwargs_inner['level']
                else:
                    lvl = 0
                msg1(message, level=lvl, end=term)
            # write log message
            write_log(message, logfile)
            # Call the original function
            return_value = fn(*args, **kwargs_inner)
            # Post-call operations
            # ...
            # Finally, return whatever fn would have returned!
            return return_value
        return wrapped
    return decorator
