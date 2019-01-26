"""
Top-level dysart feature class. Defines dependency-solving behavior at a high
level of abstraction, deferring implementation of refresh functions to user-
defined subclasses.
"""

#import Labber
from mongoengine import *
import datetime as dt
import time
from messages import *
# Decorator definitions
from functools import wraps


def refresh(fn):
	"""
	Decorator that flags a method as having dependencies and possible requiring
	a refresh operation. Recursively refreshes ancestors, then checks an
	additional condition `expired()` specified by the Feature class. If the
	feature or its ancestors have expired, perform the corrective operation
	defined by the _______ method.

	An advantage of using a refresh decorator to solve the dependency problem
	is that a given feature may have a variety of public methods with the same
	dependencies. This situation can be illustrated by a QubitRabi feature with
	public methods `pi_time` and `pi_2_time` accessed as properties:

		@property
		@refresh
		def pi_time(self):
			return self.data['pi_time']

		@property
		@refresh
		def pi_2_time(self):
			return self.data['pi_2_time']

	If we access qubit_rabi.pi_time followed by qubit_rabi.pi_2_time, they
	should use the same measurement & fit results, from a single call to the
	class's update mthod, to return these two values.

	This is a pretty central feature, and it must be done right. This should be
	a focus of any future code review, so
	"""
	@wraps(fn)
	def wrapped_fn(*args, **kwargs):
		"""
		The modified function passed to refresh.
		"""
		self = args[0]
		# Sanitize the input in case a level wasn't passed.
		if 'level' in kwargs:
			lvl = kwargs['level']
		else:
			lvl = 0
		is_stale = False
		# if this call recurses, recurse on ancestors.
		if self.is_recursive():
			for parent in self.parents:
				# TODO: implement this default refresh function
				# If an upstream feature expired, this feature needs to be
				# refreshed as well.
				parent_expired = parent.expired()
				if parent_expired:
					# Call parent to refresh recursively
					parent()
				is_stale |= parent_expired
		# If stale for some other reason, also flag to be updated.
		self_expired = self.expired()
		is_stale |= self_expired
		# Call the update-self method, the reason for this wrapper's existence
		self()
		# Call the requested function!
#TODO	#@logged(level=lvl)
		return_value = fn(*args, **kwargs)
		# Save any changes to the database
		self.save()
		# Finally, pass along return value of fn: this wrapper should be purely
		# impure
		return return_value
	return wrapped_fn


class Feature(Document):
	"""
	Device or component feature class. Each measurement should be implemented
	as a an instance of this class.
	# Note that Feature will be subclassed many times per experiment! (Though
	# hopefully reusably, if I don't mess things up!)
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

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.parents = set([])

	# Does this work? The decorator is interpreted at runtime, so self.name will
	# be in scope, right?
	@logged('update method called')
	def __call__(self):
		"""
		Feature is callable. This method does whatever is needed to update an
		expired feature.
		By default, calling the instance only refreshes
		and logs. Unless overwritten, just updates the time-since-refresh and
		returns itself. This strikes me as a convenient expressionn of intent
		in some ways, but it's also a little unpythonic: "explicit is better
		than implicit".
		"""

		self.timestamp = dt.datetime.now()
		return self

	def expired(self):
		"""
		Check for feature expiration. By default, everything is a twinkie.
		"""

		return False

	def update(self):
		pass

	def is_recursive(self):
		"""
		Does dependency-checking recurse on this feature? By default, yes.
		Even though this does nothing now, I'm leaving it here to indicate that
		a feature might take its place in the future.
		"""
		return True