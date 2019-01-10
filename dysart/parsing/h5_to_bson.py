"""

"""

import h5py
import bson

def insert_keys(doc, mapping):
	"""
	Recursively insert all a given mapping object into a dictionary `doc`.
	This is insanely slow, but I'm not sure why.
	"""
	for key in mapping.keys():
		if hasattr(mapping[key], 'keys'):
			doc_entry = {}
			insert_keys(doc_entry, mapping[key])
			doc[key] = doc_entry
		else:
			doc[key] = list(mapping[key])


def import_h5(filename):
	"""
	Takes an .hdf5 file, recursively produces a nested dictionary
	describing the document.
	"""	
	
	f = h5py.File(filename, 'r')
	doc = {}
	insert_keys(doc, f)
	return doc

def export_h5(filename):
	pass
