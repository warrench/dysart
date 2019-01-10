from mongoengine import *
import datetime

host = ('localhost', 27017)
connect('dummy_db', *host)


class Device(Document):
	timestamp = DateTimeField(default=datetime.datetime.now)
	cal_func = StringField(max_length=40)

	def cal(self):
		getattr(self, cal_func)()


class Fizzer(Device):
	carbonation = FloatField()
	decal_rate = FloatField()

	def __init__(self, p_fizzer):
		super().__init__(cal_func='cal_func')
		self.p_fizzer = p_fizzer

	def cal_func(self):
		pass


class Carbonator(Device):
	uncertainty = FloatField()

	def __init__(self, p_carbonator):
		super().__init__()
		self.p_caronator = p_carbonator

	def cal_func(self):
		pass


class Fizzmeter(Device):
	uncertainty = FloatField()

	def __init__(self, p_fizzmeter):
		super().__init__()
		self.p_fizzmeter = P_Fizzmeter

	def cal_func(self):
		pass
