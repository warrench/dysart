"""
A dummy playground to experiment and learn what doesn't work.
Here, basically all the (futre) components (except fitting) of dysart are
unfactored, and appear as a structureless blob.
"""

from pymongo import MongoClient
import h5json

# Debug database runs locally, on default port
client = MongoClient('localhost', 27017)
db = client['dummy_db']
