#! /bin/python

"""
Author: mcncm, 2019
DySART toplevel administration script
"""

from dysart.services.dyserver import Dyserver

if __name__ == '__main__':
    # Import the modules that have package dependencies, and need the
    # environment to be activated.
    from dysart.services.database import Database

    server = Dyserver()
    server._start()
