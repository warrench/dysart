"""
Standard output messages for displaying hierarchically-organized data such as
stack-based status lines.
"""

import os
import datetime as dt

default_logfile_path='../../debug_data/log/dysart.log'
indent = '   '

def msg1(message, level=0, logged=True, end="\n"):
    prompt = '=> '
    indent = '   '
    output = level*indent + prompt + message
    write_log(output)
    print(output, end=end)

def msg2(message, level=0, logged=True, end="\n"):
    prompt = '-> '
    indent = '   '
    output = level*indent + prompt + message
    write_log(output)
    print(output, end=end)

def write_log(message, logfile=default_logfile_path):
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
