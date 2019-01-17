"""
A dummy playground to experiment and learn what doesn't work.
Here, basically all the (future) components (except, critically, Labber) of the
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
fizzer_2 = Fizzer(time_const_sec=20)

# A fizzmeter
fizzmeter_1 = Fizzmeter(uncertainty=0.05,
                        response_delay=0,
                        cal_delay=0,
                        decal_time_sec=1000000)
fizzmeter_2 = Fizzmeter(uncertainty=0.00,
                        response_delay=0,
                        cal_delay=0,
                        decal_time_sec=1000000)

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
fizzmeter_driver_1 = FizzmeterDriver(name='fizz-d-1')
fizzmeter_driver_2 = FizzmeterDriver(name='fizz-d-2')

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
fizzer_1_time_const.dependencies = set({fizzmeter_driver_1})
fizzer_1_time_const.fizzmeterdriver = fizzmeter_driver_1

fizzer_2_time_const = FizzTimeConst(n_data_points=10,
                                    time_interval=0.2,
                                    name='fizz-tc-2')
fizzer_2_time_const.dependencies = set({fizzmeter_driver_2})
fizzer_2_time_const.fizzmeterdriver = fizzmeter_driver_2


print('Done.')

########################
# Do some measurements #
########################

# These are optional, and not part of the setup. If you're using this as a
# notebook template, feel free to remove or edit them.

print('Do some measurements... ')
fizzer_2_time_const.measure_time_const()
print('Done.')
tc = fizzer_2_time_const.get_time_const()
print('Fizzer 2 time constant is measured to be {:.3f} seconds.'.format(tc))

########################
# Save to the database #
########################

#fizzer_2_time_const.name='fizz-tc-2'
print('Saving result to database...', end='')
fizzer_2_time_const.save()
print('Done.')
