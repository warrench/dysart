"""
Top-level dysart feature class. Defines dependency-solving behavior at a high
level of abstraction, deferring implementation of update conditions to user-
defined subclasses.

The Feature interface is designed to be as nearly invisible as possible. The
rationale goes like this: someone---somewhere, somewhen---has to explicitly
specify the device-property dependency graph. This person (the "user") should be
protected only from thinking about more than one system layer _at a time_.
Later on, some other scientist might like to take a far-downstream measurement
without having to think about _anything_ more than the highest leayer of
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
	additional condition `__expired__()` specified by the Feature class. If the
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
		# is_stale tracks whether we need to update this node
		is_stale = False
		# if this call recurses, recurse on ancestors.
		if self.is_recursive():
			for parent in self.parents:
				# Call parent to refresh recursively; increment stack depth
				parent_is_stale = parent.touch(level=lvl + 1, is_stale=0)
				is_stale |= parent_is_stale
		# If stale for some other reason, also flag to be updated.
		self_expired = self.__expired__(level=lvl)
		is_stale |= self_expired
		# Call the update-self method, the reason for this wrapper's existence
		if is_stale:
			self(level=lvl)
		# Update staleness parameter in case it was passed in with the function
		# TODO: this currently only exists for the benefit of Feature.touch().
		# If that method is removed, consider getting rid of this snippet, too.
		if 'is_stale' in kwargs:
			kwargs['is_stale'] = is_stale
		# Call the requested function!
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
	as an instance of this class.
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
	parents = ListField(default=[])

	def __init__(self, **kwargs):
		super().__init__(**kwargs)
		self.save()

	# Does this work? The decorator is interpreted at runtime, so self.name will
	# be in scope, right?
	@logged('update method called')
	def __call__(self, level=0):
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
		return

	@refresh
	def touch(self, level=0, is_stale=False):
		"""
		Manually refresh the feature without doing anything else. This method
		has a special role, being invoked by DySART as the default refresh
		method called as it climbs the feature tree. It's also treated in a
		special way by @refresh, in order to propagate refresh data downstream.
		While this does work, it's a little bit unpythonic: "explicit is better
		than implicit".
		In short, this is a hack, and it shouldn't last.
		"""
		return is_stale

	def __expired__(self, level=0):
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

	def add_parents(self, *new_parents):
		"""
		Insert a dependency into the feature's parents list and write to the
		database. Can pass a single feature, multiple features as
		comma-separated parameters, a list of features, a list of list of
		features, and so on.
		"""
		for parent in new_parents:
			# Handle (arbitrarily deeply nested) lists of parents.
			# This works with explicit type-checking, but it's not the most
			# pythonic solution in the world. Could be done more canonically
			# Feature weren't iterable!
			if isinstance(parent, Feature):
				if parent not in self.parents:
					print("ok, adding a parent!")
					self.parents.append(parent)
			else:
				self.add_parents(*parent)
		self.save()
