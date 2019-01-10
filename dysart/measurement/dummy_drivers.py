"""
Virtual device wrappers for the dummy lab. This is sort of how I imagine
the DySART interface working in a final version "in spirit", only maybe written
a little more cleanly!
"""

from dysart.fitting.exponential import *
from mongoengine import *
import datetime

# Open a connection to the Mongo database
host_data = ('localhost', 27017)
connect('dummy_db', host=host_data[0], port=host_data[1])

########################
# Features and devices #
########################

class Feature(Document):
	"""
	Device or component feature class. Each "measurement" should be implemented
	as a an instance of such a class.
	"""

	meta = {'allow_inheritance': True}

	# Feature payload. One of the drawbacks of using mongoengine is that the
	# structure of the payload is pretty constrained, and on top of that I
	# don't really know how it is represented by the database.
	# Hence "data" as a blob.
	name = StringField(required=True, max_length=40)
	data = DictField()

	# Time when last updated
	timestamp = DateTimeField(default=datetime.datetime.now())
	is_stale_func = StringField(max_length=40)
	refresh_func = StringField(max_length=40)
	dependencies = StringField()

	def is_stale(self):
		"""
		A function implemented or provided by the instance. As written, this is
		not a safe or robust way to do this at all, but it conveys the goal,
		is as simple as possible, and is probably more secure than saving a
		lambda expression to the database.

		Here are other ways to solve the problem:
		* Save function literals as data
		* Make a new subclass for each feature type (as devices below)

		Each of these has problems, and there's probably one that's better,
		but this is a rough prototype, so it's ok for now.
		"""
		eval(self.is_stale_func + '()')

	def refresh(self):
		"""
		ibid
		"""
		eval(self.refresh_func + '()')

	##############################
	# `is_stale` implementations #
	##############################

	def aged_out(self):
		"""
		Check whether timestamp is too old.
		"""
		t_now = datetime.datetime.now()
		delta_t = t_now - self.timestamp
		return delta_t > self.time_out

	def dependencies_stale(self):
		"""
		Recursively check whether dependencies have gone stale
		"""
		for dep in self.dependencies:
			if dep.is_stale():
				return True

	def dependencies_or_age(self):
		"""
		Either dependencies have gone stale or it has aged out
		"""
		return self.aged_out() or self.dependencies_stale()

		#############################
		# `refresh` implementations #
		#############################

	def refresh_dependencies(self):
		"""
		Recursively refresh all dependencies and reset timestamp. Note how silly it
		is that this traverses the whole tree already visited by dependencies_stale!
		"""
		for dep in self.dependencies:
			if dep.is_stale():
				dep.refresh()
		self.timestamp = datetime.datetime.now()


class Device:
	#meta = {'allow_inheritance': True}
	#timestamp = DateTimeField(default=datetime.datetime.now())
	#cal_func = StringField(max_length=40)
	#connect_func = StringField(max_length=40)
	#
	#def cal(self):
	#	"""
	#	ibid
	#	"""
	#	getattr(self, self.cal_func)()
	#
	#def connect(self, addr):
	#	"""
	#	ibid
	#	"""
	#	getattr(self, self.connect_func)(addr)

	def __init__(self):
		pass


#class Fizzer(Device):
#	carbonation = FloatField()
#	decal_rate = FloatField()
#
#	def __init__(self):
#		super().__init__()
#
#	def cal_func(self):
#		pass
#
#	def connect(self, addr):
#		self.p_fizzer = addr
#

class CarbonatorDriver(Device):

	def __init__(self):
		super().__init__()

	def cal_func(self):
		pass

	def connect(self, addr):
		self.carbonator = addr

	def carbonate(self, fizzer, carbonation):
		result = self.carbonator.carbonate(carbonation)
		return result


class FizzmeterDriver(Device):

	def __init__(self):
		super().__init__()

	def cal_func(self):
		pass

	def connect(self, addr):
		self.fizzmeter = addr

	def measure(self):
		result = self.fizzmeter.measure()
		return result

	def get_measurement(self, i):
		return self.fizzmeter.measurements[i]

	def calibrate(self):
		print("Calibrating fizzmeter... ", end="")
		self.fizzmeter.calibrate()
		print("Done.")
