"""
Proof-of-principle MongoDB database for test laboratory.
NB virtual devices should be implemented with Labber, rather than whatever
ad-hoc solution I come up with now. For this reason it is essential to do
at least some of this work on my old mac, or work with Simon to get Labber
running on Linux.
"""

from pymongo import MongoClient

# Debug database runs locally, on default port
client = MongoClient('localhost', 27017)
db = client['debug_db']
