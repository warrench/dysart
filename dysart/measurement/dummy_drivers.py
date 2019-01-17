"""
Virtual device wrappers for the dummy lab. This is sort of how I imagine
the DySART interface working in a final version "in spirit", only maybe written
a little more cleanly!
"""

from fitting.exponential import *
from mongoengine import *
import datetime as dt
import time
from messages import *

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
	name = StringField()
	data = DictField()

	# Time when last updated
	timestamp = DateTimeField(default=dt.datetime.now())
	is_stale_func = StringField(max_length=60)
	refresh_func = StringField(max_length=60)

	def is_stale(self, level=0):
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
		return eval(self.is_stale_func + '(self, level=level)')

	def refresh(self, level=0):
		"""
		ibid
		"""
		return eval(self.refresh_func + '(self, level=level)')

	##############################
	# `is_stale` implementations #
	##############################

	def aged_out(self, level=0):
		"""
		Check whether timestamp is too old.
		"""
		t_now = dt.datetime.now()
		delta_t = t_now - self.timestamp
		return delta_t > self.age_out_time

	def dependencies_stale(self, level=0):
		"""
		Recursively check whether dependencies have gone stale
		"""
		for dep in self.dependencies:
			if dep.is_stale(level=level):
				return True
		return False

	def dependencies_or_age(self, level=0):
		"""
		Either dependencies have gone stale or it has aged out
		"""
		return self.aged_out(level=level) or self.dependencies_stale(level=level)

		#############################
		# `refresh` implementations #
		#############################

	def refresh_dependencies(self, level=0):
		"""
		Recursively refresh all dependencies and reset timestamp. Note how silly it
		is that this traverses the whole tree already visited by dependencies_stale!
		"""
		for dep in self.dependencies:
			if dep.is_stale(level=level):
				dep.refresh(level=level)
		self.timestamp = dt.datetime.now()


class FizzTimeConst(Feature):
	"""
	Feature class for  the time constant of a fizzer attached to an associated
	FizzMeterDriver, self.fizzmeterdriver.
	"""

	is_stale_func = StringField(default='Feature.dependencies_stale', max_length=60)
	refresh_func = StringField(default='FizzTimeConst.refresh', max_length=60)
	data = DictField(default=
						{
							'fizziness': [],
							'exp_fit_result': []
						}
					)
	time_interval = FloatField()
	n_data_points = IntField()


#	def __init__(self, **kwargs):
#		super().__init__(**kwargs)
#		self.refresh_func = 'FizzTimeConst.refresh'
#		self.is_stale_func = 'Feature.dependencies_stale'

	def refresh(self, level=0):
		self.refresh_dependencies(level=level+1)
		self.measure_time_const(level=level+1)

	def measure_fizziness(self, level=0):
		"""
		Measures the fizziness of a fizzer and inserts it into the Feature's
		record of fizziness measurements in self.data
		"""
		msg2("measuring fizziness... ", level=level, end='')
		self.fizzmeterdriver.measure()
		fizziness = self.fizzmeterdriver.get_last_measurement()
		print("{:.3f}".format(fizziness))
		data_entry = (dt.datetime.now(), fizziness)
		if self.data['fizziness'] is None:
			self.data['fizziness'] = [data_entry]
		else:
			self.data['fizziness'].append(data_entry)
		return

	def measure_time_const(self, level=0):
		"""
		Performs a sequence of fizziness measurements; retrieves the values
		and fits the measured values to a decaying exponential. Records the
		time constant in the Feature's data field.
		"""
		msg1("measuring time constant.", level=level)
		self.fizzmeterdriver.clear_measurements()
		for _ in range(self.n_data_points):
				self.measure_fizziness(level=level+1)
				time.sleep(self.time_interval)
		meas_ = self.data['fizziness'][-self.n_data_points:]
		# Times from start in seconds
		x = np.array([(m[0] - meas_[0][0]).total_seconds() for m in meas_])
		# Measured fizzinesses
		y = np.array([m[1] for m in meas_])
		fit_result = fit_exponential(x, y)

		fit_result_dict = {
		'decay': fit_result.params['decay'].value,
		'amplitude': fit_result.params['amplitude'].value
		}

		data_entry = (dt.datetime.now(), fit_result_dict)
		self.data['exp_fit_result'].append(data_entry)

		return

	def get_time_const(self):
		msg1('getting time constant.', level=0)
		if self.is_stale():
				self.refresh(level=0)
		return self.data['exp_fit_result'][-1][1]['decay']


class CarbonatorDriver(Feature):

	def cal_func(self):
		pass

	def connect(self, addr):
		self.carbonator = addr

	def carbonate(self, fizzer, carbonation):
		result = self.carbonator.carbonate(carbonation)
		return result


class FizzmeterDriver(Feature):
	"""
	Controller for a Fizzmeter.
	"""

	name = StringField()
	timestamp = DateTimeField(default=dt.datetime.now())
	is_stale_func = StringField(default='FizzmeterDriver.fizzmeter_uncalibrated', max_length=60)
	refresh_func = StringField(default='FizzmeterDriver.calibrate', max_length=60)
	decal_tolerance = 0.01

	def fizzmeter_uncalibrated(self, level=0):
		decal_time_sec = self.fizzmeter.decal_time_sec
		cal_time = self.fizzmeter.cal_time
		now_time = dt.datetime.now()
		elapsed_time = (now_time - cal_time).total_seconds()
		return elapsed_time > np.sqrt(decal_time_sec) * self.decal_tolerance

	def calibrate(self, level=0):
		msg1("calibrating fizzmeter.", level=level)
		self.fizzmeter.calibrate()
		self.timestamp = dt.datetime.now()

	def cal_func(self):
		pass

	def connect(self, addr):
		self.fizzmeter = addr

	def measure(self):
		result = self.fizzmeter.measure()
		return result

	def clear_measurements(self):
		self.fizzmeter.clear_measurements()
		return

	def get_measurement(self, i):
		return self.fizzmeter.measurements[i]

	def get_last_measurement(self):
		return self.fizzmeter.measurements[-1]
