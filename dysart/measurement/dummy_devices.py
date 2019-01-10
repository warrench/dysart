"""
Virtual device wrappers for the dummy lab. This is approximately how I imagine
the DySART interface working in a final version, only better written!
"""

from mongoengine import *
import datetime

# Open a connection to the Mongo database
host_data = ('localhost', 27017)
connect('dummy_db', host=host_data[0], port=host_data[1])

class Feature(Document):
	"""
	Device or component feature class. Each "measurement" should be implemented
	as a an instance of such a class.
	"""
	meta = {'allow_inheritance': True}
	name = StringField(required=True, max_length=40)
	is_stale_func = StringField(max_length=40)
	refresh_func = StringField(max_length=40)
	dependencies = StringField()

	def is_stale(self):
		"""
		A function implemented by the class instance
		eval(self)


class Device(Document):
	meta = {'allow_inheritance': True}
	timestamp = DateTimeField(default=datetime.datetime.now)
	cal_func = StringField(max_length=40)
	connect_func = StringField(max_length=40)

	def cal(self):
		"""
		This method retrieves the name of the calibration function from the
		database and executes that function. Each virtual device class should
		implement a calibration function.
		"""
		getattr(self, self.cal_func)()

	def connect(self, addr):
		"""
		This method retrieves the name of the connection function from the
		database and executes that function. Each virtual device class should
		implement a calibration function.
		"""
		getattr(self, self.connect_func)(addr)


class Fizzer(Device):
	carbonation = FloatField()
	decal_rate = FloatField()

	def __init__(self):
		super().__init__(cal_func='cal_func', connect_func='open_connection')

	def cal_func(self):
		pass

	def open_connection(self, addr):
		self.p_fizzer = addr


class Carbonator(Device):
	uncertainty = FloatField()

	def __init__(self, p_carbonator):
		super().__init__(cal_func='cal_func', connect_func='open_connection')
		self.p_caronator = p_carbonator

	def cal_func(self):
		pass

	def open_connection(self, addr):
		pass


class Fizzmeter(Device):
	uncertainty = FloatField()

	def __init__(self, p_fizzmeter):
		super().__init__(cal_func='cal_func', connect_func='open_connection')
		self.p_fizzmeter = P_Fizzmeter

	def cal_func(self):
		pass

	def open_connection(self, addr):
		pass
