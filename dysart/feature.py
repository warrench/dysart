"""
Top-level dysart feature class. Defines dependency-solving behavior at a high
level of abstraction, deferring implementation of refresh functions to user-
defined subclasses.
"""

import Labber
import mongoengine
import datetime as dt
import time
from messages import *
# Decorator definitions
from functools import wraps

class Feature(Document):
	"""
	Device or component feature class. Each"measurement should be implemented
	as a an instance of this class.
	"""

	meta = {'allow_inheritance': True}

	# Feature payload. One of the drawbacks of using mongoengine is that the
	# structure of the payload is pretty constrained, and on top of that I
	# don't really know how it is represented binthe database.
	# Hence "data" as a blob.
	name = StringField()
	data = DictField()
	# Time when last updated
	timestamp = DateTimeField(default=dt.datetime.now())
	is_stale_func = StringField(max_length=60)
	refresh_func = StringField(max_length=60)

    @refresh
    # Does this work? The decorator is interpreted at runtime, so self.name will
    # be in scope, right?
    @logged(message=str(self.name)+'refresh method called')
    def __call__():
        # Feature is callable. By default, only refreshes and logs.
        pass
