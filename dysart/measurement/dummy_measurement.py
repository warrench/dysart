"""
A dummy playground to experiment and learn what doesn't work.
Here, basically all the (futre) components (except, critically, Labber) of the
system are present in at least some inchoate form. There's a lot of "printf
debugging" in here, which may not conform to best practices in general, but it
is pretty handy for a demonstration like this.
"""

from dummy_lab import *
from dummy_devices import *
# Use mongoengine, MongoDB's ODM ("Object-Document Mapper"), which is something
# like an ORM for a document-based noSQL database. This doesn't let me easily
# implement all the features I would like, including VCS-like stage/commit
# and branching of configuration changes, but the high-level API is good enough
# for a crude proof of principle, which this script is.
from mongoengine import *

# Open a connection to the Mongo database
host_data = ('localhost', 27017)
connect('dummy_db', host=host_data[0], port=host_data[1])

#####################################
# Set up the "physical" lab devices #
#####################################

print('Setting up the lab... ', end='')

# Fizzers
p_fizzer_1 = P_Fizzer(time_const_sec=1)
p_fizzer_2 = P_Fizzer(time_const_sec=10)

# A fizzmeter
p_fizzmeter = P_Fizzmeter(uncertainty=0.05)

# A carbonator
p_carbonator = P_Fizzmeter(uncertainty=0.1)

print('Done.')

####################################
# Set up the "virtual" lab devices #
####################################

print('Creating virtual devices... ', end='')

# Fizzers
fizzer_1 = Fizzer()
fizzer_2 = Fizzer()

# A Fizzmeter
fizzmeter = Fizzmeter()

# A carbonator
carbonator = Carbonator()

print('Done.')

############################################
# Connect virtual devices to physical ones #
############################################

print('Connecting virtual devices to lab... ', end='')

# Fizzers
fizzer_1.connect(p_fizzer_1)
fizzer_2.connect(p_fizzer_2)

# Fizzmeter
fizzmeter.connect(p_fizzmeter)

# Carbonator
carbonator.connect(p_carbonator)

print('Done.')

######################
# Build feature tree #
######################

# print('Building feature tree...', end='')

# print('Done.')

########################
# Do some measurements #
########################
