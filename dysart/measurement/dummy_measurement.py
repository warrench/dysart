"""
A dummy playground to experiment and learn what doesn't work.
Here, basically all the (futre) components (except, critically, Labber) of the
system are present in at least some inchoate form. There's a lot of "printf
debugging" in here, which may not conform to best practices in general, but it
is pretty handy for a demonstration like this.
"""
import datetime as dt
from dummy_lab import *
from dummy_drivers import *
"""
Use mongoengine, MongoDB's ODM ("Object-Document Mapper"), which is something
like an ORM for a document-based noSQL database. This doesn't let me easily
implement all the features I would like, including VCS-like stage/commit
and branching of configuration changes, but the high-level API is good enough
for a crude proof of principle, which this script is.
"""
from mongoengine import *

# Open a connection to the Mongo database
host_data = ('localhost', 27017)
connect('dummy_db', host=host_data[0], port=host_data[1])

#####################################
# set up the "physical" lab devices #
#####################################

print('Setting up the lab... ', end='')

# Fizzers
fizzer_1 = Fizzer(time_const_sec=1)
fizzer_2 = Fizzer(time_const_sec=10)

# A fizzmeter
fizzmeter_1 = Fizzmeter(uncertainty=0.05,
                        response_delay=0)
fizzmeter_2 = Fizzmeter(uncertainty=0.00,
                        response_delay=0)

# A carbonator
carbonator = Carbonator(uncertainty=0.1)

# Put the fizzers into the fizzmeters
fizzmeter_1.attach_fizzer(fizzer_1)
fizzmeter_2.attach_fizzer(fizzer_2)

print('Done.')

####################################
# set up the "virtual" lab devices #
####################################

print('Creating virtual devices... ', end='')

# A Fizzmeter
fizzmeter_driver_1 = FizzmeterDriver()
fizzmeter_driver_2 = FizzmeterDriver()

# A carbonator
carbonator_driver = CarbonatorDriver()

print('Done.')

############################################
# Connect virtual devices to physical ones #
############################################

print('Connecting virtual devices to lab... ', end='')

# Fizzmeters
fizzmeter_driver_1.connect(fizzmeter_1)
fizzmeter_driver_2.connect(fizzmeter_2)

# Carbonator
carbonator_driver.connect(carbonator)

print('Done.')

######################
# Build feature tree #
######################

"""
The simple feature-tree structure we'll be using for this example has the
following structure (inheritance goes top to bottom):

                         fizzmeter i calibration
                           /              |
                          /               |
             carbonator calibration       |
                          \               |
                           \              |
                         fizzer i time constant
"""

print('Building feature tree...', end='')

"""
This is a lot of boilerplate even for a simple system!
"""

# Fizzer time constants
# TODO: Why does name setting not work? Understand how update() func works.
fizzer_1_time_const = FizzTimeConst(n_data_points=10,
                                    time_interval=0.1,
                                    name='fizz-tc-1')
fizzer_1_time_const.dependencies = set({})
fizzer_1_time_const.fizzmeterdriver = fizzmeter_driver_1

fizzer_2_time_const = FizzTimeConst(n_data_points=10,
                                    time_interval=0.2,
                                    name='fizz-tc-2')
fizzer_2_time_const.dependencies = set({})
fizzer_2_time_const.fizzmeterdriver = fizzmeter_driver_2

# Fizzmeter calibration and uncertainty
fizzmeter_1_cal = Feature()
fizzmeter_1_cal.dependencies = set({})
fizzmeter_1_cal.fizzmeterdriver = fizzmeter_driver_1
fizzmeter_1_unc = Feature()
fizzmeter_1_unc.dependencies = set({})
fizzmeter_1_unc.fizzmeterdriver = fizzmeter_driver_1

fizzmeter_2_cal = Feature()
fizzmeter_2_cal.dependencies = set({})
fizzmeter_2_cal.fizzmeterdriver = fizzmeter_driver_2
fizzmeter_2_unc = Feature()
fizzmeter_2_unc.dependencies = set({})
fizzmeter_2_unc.fizzmeterdriver = fizzmeter_driver_2

# Carbonator calibration and uncertainty
carbonator_cal = Feature()
carbonator_cal.dependencies = set({})
carbonator_cal.carbonator_driver = carbonator_driver
carbonator_unc = Feature()
carbonator_unc.dependencies = set({})
carbonator_unc.carbonator_driver = carbonator_driver

# set dependencies
fizzer_1_time_const.dependencies.add(fizzmeter_1_cal)
fizzer_1_time_const.dependencies.add(carbonator_cal)

fizzer_1_time_const.dependencies.add(fizzmeter_2_cal)
fizzer_1_time_const.dependencies.add(carbonator_cal)

carbonator_cal.dependencies.add(fizzmeter_1_cal)
carbonator_cal.dependencies.add(fizzmeter_2_cal)

# set staleness policies
fizzer_1_time_const.is_stale_func = 'self.dependencies_stale'
fizzer_2_time_const.is_stale_func = 'self.dependencies_stale'

fizzmeter_1_cal.is_stale_func = 'self.aged_out'
fizzmeter_1_cal.age_out_time = dt.timedelta(seconds=
    1 / fizzmeter_1_cal.fizzmeterdriver.fizzmeter.decal_rate
)
fizzmeter_2_cal.is_stale_func = 'self.aged_out'
fizzmeter_2_cal.age_out_time = dt.timedelta(seconds=
    1 / fizzmeter_2_cal.fizzmeterdriver.fizzmeter.decal_rate
)

carbonator_cal.is_stale_func = 'self.dependencies_stale'

# set refresh policies
fizzer_1_time_const.refresh_func = 'self.refresh_dependencies'
fizzer_2_time_const.refresh_func = 'self.refresh_dependencies'

carbonator_cal.refresh_func = 'self.refresh_dependencies'

fizzmeter_1_cal.refresh_func = 'fizzmeter_driver_1.calibrate'
fizzmeter_2_cal.refresh_func = 'fizzmeter_driver_2.calibrate'

print('Done.')

########################
# Do some measurements #
########################

print('Do some measurements... ')
fizzer_2_time_const.measure_time_const()
print('Done.')
tc = fizzer_2_time_const.data['exp_fit_result'][0][1]['decay']
print('Fizzer 2 time constant is measured to be {} seconds.'.format(tc))

########################
# Save to the database #
########################

fizzer_2_time_const.name='fizz-tc-2'
print('Saving result to database...', end='')
fizzer_2_time_const.save()
print('Done.')
