"""
Standard output messages for displaying hierarchically-organized data such as
stack-based status lines.
"""

import os
import datetime as dt
from functools import wraps

default_logfile_path=os.path.join('..','..','debug_data','log','dysart.log')

def msg1(message, level=0, end="\n"):
    prompt = '=> '
    indent = '   '
    output = level*indent + prompt + message
    print(output, end=end)

def msg2(message, level=0, end="\n"):
    prompt = '-> '
    indent = '   '
    output = level*indent + prompt + message
    print(output, end=end)

def write_log(message, logfile):
    """
    For now, just appends lines to the default log file.
    """
    # TODO: use python standard library logging API to log message "correctly"
    separator = ' | '
    prefix = dt.datetime.now().ctime() + separator
    fn = os.path.join(os.path.dirname(__file__), logfile)
    f = open(logfile, 'a')
    f.write(prefix + message + '\n')
    f.close()

def logged(logfile=default_logfile_path, stdout=True, message='log event'):
    """
    decorator for handling log messages.
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
            fn(*args, **kwargs)
            # Post-call operations
            # ...
        return wrapped
    return decorator
