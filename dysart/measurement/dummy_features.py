"""
Virtual device wrappers for the dummy lab. This is sort of how I imagine
the DySART interface working in a final version "in spirit", only maybe written
a little more cleanly!
"""

from fitting.exponential import *
from feature import *
from mongoengine import *
import datetime as dt
import time
from messages import *


########################
# Features and devices #
########################

class FizzTimeConst(Feature):
	"""
	Feature class for  the time constant of a fizzer attached to an associated
	fm_cont, self.fm_cont.
	"""

	data = DictField(default={'fizziness': [], 'exp_fit_result': []})
	time_interval = FloatField()
	n_data_points = IntField()

	@logged(message='measuring fizziness... ')
	def measure_fizziness(self, level=0):
		"""
		Measures the fizziness of a fizzer and inserts it into the Feature's
		record of fizziness measurements in self.data
		"""
		self.fm_cont.measure()
		fizziness = self.fm_cont.get_last_measurement()
		print("{:.3f}".format(fizziness))
		data_entry = (dt.datetime.now(), fizziness)
		if self.data['fizziness'] is None:
			self.data['fizziness'] = [data_entry]
		else:
			self.data['fizziness'].append(data_entry)
		return

	@logged(message='measuring time constant.')
	def measure_time_const(self, level=0):
		"""
		Performs a sequence of fizziness measurements; retrieves the values
		and fits the measured values to a decaying exponential. Records the
		time constant in the Feature's data field.
		"""
		self.fm_cont.clear_measurements()
		for _ in range(self.n_data_points):
				self.measure_fizziness(level=level + 1)
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

	def no_recorded_result(self):
		"""
		Expiration condition for FizzTimeConst: is there a result?
		"""
		return 'exp_fit_result' in self.data

	@property
	@refresh
	@logged(message='getting time constant... ')
	def time_const(self):
		"""
		Get the time constant from the last measurement performed. Triggers a
		measurement if self or any parents is expired.
		"""
		return self.data['exp_fit_result'][-1][1]['decay']

	# Which methods are used to check for expriation and updating the object?
	__call__ = measure_time_const
	expired = no_recorded_result


class CarbonatorController(Feature):

	def cal_func(self):
		pass

	@logged(message='connecting to carbonator... ')
	def connect(self, addr):
		self.carbonator = addr

	def carbonate(self, fizzer, carbonation):
		result = self.carbonator.carbonate(carbonation)
		return result


class FizzmeterController(Feature):
	"""
	Controller for a Fizzmeter. It's not clear to me if this must be a Feature.
	"""

	name = StringField()
	timestamp = DateTimeField(default=dt.datetime.now())
	decal_tolerance = 0.01

	def fizzmeter_uncalibrated(self, level=0):
		decal_time_sec = self.fizzmeter.decal_time_sec
		cal_time = self.fizzmeter.cal_time
		now_time = dt.datetime.now()
		elapsed_time = (now_time - cal_time).total_seconds()
		return elapsed_time > np.sqrt(decal_time_sec) * self.decal_tolerance

	@logged(message='calibrating fizzmeter... ')
	def calibrate(self, level=0):
		self.fizzmeter.calibrate()
		self.timestamp = dt.datetime.now()

	def cal_func(self):
		pass

	@logged(message='connecting to fizzmeter... ')
	def connect(self, addr):
		self.fizzmeter = addr

	#@logged(message='measuring fizziness... ')
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

	# Which methods are used to check for expriation and updating the object?
	__call__ = calibrate
	expired = fizzmeter_uncalibrated
