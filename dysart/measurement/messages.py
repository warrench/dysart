"""
Standard output messages for displaying hierarchically-organized data such as
recursively-called status lines.
"""

import os
import datetime as dt
from functools import wraps

default_logfile_path = os.path.join('..', '..', 'debug_data',
                                    'log', 'dysart.log')


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
    fullpath = os.path.join(os.path.dirname(__file__), logfile)
    with open(fullpath, 'a') as f:
        f.write(prefix + message + '\n')


def logged(logfile=default_logfile_path, stdout=True, message='log event'):
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

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args, **kwargs):
            # write stdout message
            if stdout:
                if 'level' in kwargs:
                    lvl = kwargs['level']
                else:
                    lvl = 0
                msg1(message, level=lvl)
            # write log message
            write_log(message, logfile)
            # Call the original function
            return_value = fn(*args, **kwargs)
            # Post-call operations
            # ...
            # Finally, return whatever fn would have returned!
            return return_value
        return wrapped
    return decorator
