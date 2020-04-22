"""
Author: mcncm, 2019
Standard output messages for displaying hierarchically-organized data such as
recursively-called status lines.
"""

import os
import sys
import datetime as dt
from functools import wraps
import getpass
import inspect
from io import StringIO
import logging
import platform
import textwrap

import toplevel.conf as conf
from dysart.messages.errors import DysartError

DEFAULT_COL = 48
TAB = ' ' * 4


class Bcolor:
    """
    Enum for colored printing
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


def cstr_ansi(s: str, status: str = 'normal') -> str:
    """
    Wrap a string with ANSI color annotations
    TODO there's a package for this; you can rip this out.
    """
    if platform.system() == 'Windows':
        return s  # ANSI colors unsupported on Windows

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


def cstr_slack(s: str, status: str = 'normal') -> str:
    """
    Wrap a string with ANSI color annotations
    TODO there's a package for this; you can rip this out.
    """
    if status == 'bold':
        return '*' + s + '*'
    elif status == 'italic':
        return '_' + s + '_'
    elif status == 'strikethrough':
        return '~' + s + '~'
    elif status == 'underline':
        return Bcolor.UNDERLINE + s + Bcolor.ENDC
    elif status == 'code':
        return '`' + s + '`'
    elif status == 'codeblock':
        return '```' + s + '```'
    else:
        return s

# This module-scoped function is used to decorate text with colors, bold and
# italics, and so on. By default it is set to a function using ANSI escape
# codes. Context managers within this module may contextually replace it with
# a different function.
#
# I'm not convinced that this is the best approach to this problem. If you
# happen to read this and have other ideas, let's talk.
cstr = cstr_ansi

class FormatContext:
    """
    Todo: make this 100x less hacky
    """
    
    cstrs = {
        'slack': cstr_slack
    }
    
    def __init__(self, context: str):
        assert context in FormatContext.cstrs
        self.cstr = FormatContext.cstrs[context]
        
    def __enter__(self):
        global cstr
        self.old_cstr = cstr
        cstr = self.cstr
        
    def __exit__(self, *exc):
        global cstr
        cstr = self.old_cstr


def cprint(s: str, status: str = 'normal', **kwargs):
    """
    Print a string with ANSI color annotations
    """
    print(cstr(s, status), **kwargs)


def msg1(message: str, level=0, end="\n"):
    """
    Print a formatted message to stdout.
    Accepts an optional level parameter, which is useful when you might wish
    to log a stack trace.
    """
    prompt = '=> '
    indent = '   '
    output = level * indent + prompt + message
    print(output, end=end)


def msg2(message: str, level=0, end="\n"):
    """
    Print a formatted message to stdout.
    Accepts an optional level parameter, which is useful when you might wish
    to log a stack trace.
    """
    prompt = '-> '
    indent = '   '
    output = level * indent + prompt + message
    print(output, end=end)


def write_log(message: str):
    """
    Write a message to a log file with date and time information.
    """
    logging.info(message)


def logged(stdout=True, message='log event', **kwargs):
    """
    Decorator for handling log messages. By default, writes to a default log
    file in the debug_data database directory, and prints output to stdout.
    Passes level parameter in decorated function to message functions to
    """
    # set terminator for log message
    term = "\n"
    if 'end' in kwargs:
        term = kwargs['end']

    def decorator(fn):
        @wraps(fn)
        def wrapped(*args_inner, **kwargs_inner):
            if stdout:
                if 'level' in kwargs_inner:
                    lvl = kwargs_inner['level']
                else:
                    lvl = 0
                msg1(message, level=lvl, end=term)

            # Check if this was called as a method of an object and, if so,
            # intercept the message to reflect this.
            # TODO: this could done much better with a log-entry object that
            # receives attributes like 'caller', etc., and is then formatted
            # independently.
            msg_prefix = ''
            spec = inspect.getargspec(fn)
            if spec.args and spec.args[0] == 'self':
                # TODO: note that this isn't really airtight. It is not a rule
                # of the syntax that argument 0 must be called 'self' for a
                # class method.
                caller = args_inner[0]
                msg_prefix = caller.name + ' | '

            # write log message
            write_log(msg_prefix + message)
            # call the original function
            return_value = fn(*args_inner, **kwargs_inner)
            # post-call operations
            # ...
            # finally, return whatever fn would have returned!
            return return_value
        return wrapped
    return decorator


def configure_logging(logfile=''):
    """
    Set up the logging module to write to the correct logfile, etc.
    """

    if logfile == '' or logfile is None:
        # Set the log output to the null file. This should actually be cross-
        # platform, i.e. equal to '/dev/null' on unix systems and 'NULL' on
        # windows.
        logfile = os.devnull

    # TODO: I should really take advantage of some of the more advanced
    # features of the logging module.
    user = getpass.getuser()
    log_format = '%(asctime)s | ' + user + " | %(message)s"
    date_format = '%m/%d/%Y %I:%M:%S'
    logging.basicConfig(format=log_format, filename=logfile,
                        datefmt=date_format, level='INFO')


def tree(obj, get_deps: callable, pipe='│', dash='─', tee='├',
         elbow='└', indent=' ' * 3, prefix='') -> str:
    """Takes an object and a closure that is assumed to return an iterable of
    dependent objects of the same type; produces an ascii tree diagram.
    """
    s = str(obj)
    deps = list(get_deps(obj))

    # special case for empty dependents: no pipes
    if not deps:
        ('\n' + prefix).join(s.split('\n'))
        return s

    # otherwise, dependents are nonempty: pipe to them
    s = (prefix + '\n' + pipe).join(s.split('\n'))
    s += '\n'

    for i, dep in enumerate(deps):
        if i == len(deps) - 1:
            leader = elbow + dash * len(indent)
        else:
            leader = tee + dash * len(indent)

        s += prefix + leader
        new_prefix = pipe + indent if i != len(deps) - 1 else ' ' + indent
        subtree = tree(dep, get_deps, prefix=new_prefix)
        s += ('\n' + new_prefix).join(subtree.split('\n'))
    return s


def pprint_func(name: str, doc: str) -> None:
    """
    TODO real docstring for pprint_property
    Takes a name and docstring of a function and formats and pretty-prints them.
    """
    if doc is None:
        return
    # Number of columns in the formatted docscring
    status_col = int(conf.config.get('STATUS_COL') or DEFAULT_COL)
    # Prepare the docstring: fix up whitespace for display
    doc = ' '.join(doc.strip().split())
    # Prepare the docstring: wrap it and indent it
    doc = '\t' + '\n\t'.join(textwrap.wrap(doc, status_col))
    # Finally, print the result
    print(cstr(name, status='bold') + '\n' + cstr(doc, status='italic') + '\n')


class StatusMessage:
    """
    A simple context manager for printing informative status messages about
    ongoing administration tasks.

    TODO: document parameters, etc.
    """

    def __init__(self, infostr: str, donestr: str = 'done.',
                 failstr: str = 'failed.', capture_io: bool = True):
        self.infostr = infostr
        self.donestr = donestr
        self.failstr = donestr
        self.num_cols = max(int(conf.config.get('STATUS_COL') or DEFAULT_COL),
                            len(infostr))
        self.status = 'ok'
        self.__old_stdout, self.__old_stderr = sys.stdout, sys.stderr
        self.__capture_io = capture_io

    def __enter__(self):
        """Prints a message describing the action taken and redirects io"""
        cprint(self.infostr.ljust(self.num_cols).capitalize(), status='normal',
               end='', flush=True)
        if self.__capture_io:
            sys.stdout = self.stdout_buff = StringIO()
            sys.stderr = self.stderr_buff = StringIO()

    def __exit__(self, exc_type, exc_value, traceback):
        """Prints the terminating status string and restores io"""
        if exc_type is None:
            cprint(self.donestr, status='ok', file=self.__old_stdout)
        else:
            status = 'fail'
            failstr = self.failstr
            if isinstance(exc_value, DysartError):
                status = exc_value.status
                failstr = exc_value.message
            cprint(failstr, status, file=self.__old_stdout)
            if 'VERBOSE_MESSAGES' in conf.config:
                print(exc_value)
        if self.__capture_io:
            sys.stdout, sys.stderr = self.__old_stdout, self.__old_stderr
            sys.stdout.write(self.stdout_buff.getvalue())
            sys.stderr.write(self.stderr_buff.getvalue())
        return True

