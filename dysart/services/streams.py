"""
Output streams accessible to a user for visualizing status, outputs
"""

import os
import io
import sys
from queue import Queue
from typing import Optional


class DysDataStream:
    """
    Not really a stream, doesn't inherit from io.BytesIO.
    ~A singleton queue.
    """

    instance = None

    def __init__(self, *args, **kwargs):
        if not DysDataStream.instance:
            DysDataStream.instance = Queue(*args, **kwargs)
        else:
            pass  # possibly change this?

    def __getattr__(self, name):
        return getattr(DysDataStream.instance, name)

    def __setattr__(self, name, val):
        setattr(DysDataStream.instance, name, val)


def _get_stdimg() -> Optional[io.TextIOWrapper]:
    return open(os.devnull, 'wb')


def _get_stdmsg() -> Optional[io.TextIOWrapper]:
    return open(os.devnull, 'wb')


def _get_stdfit() -> Optional[io.TextIOWrapper]:
    return open(os.devnull, 'wb')


stdimg = _get_stdimg()
stdmsg = sys.stdout  # _get_stdmsg()
stdfit = _get_stdfit()
