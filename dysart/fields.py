"""
author: mcncm 2019
This is a wrapper class to allow the use of complex numbers with mongoengine.
It's not pretty, and I didn't want to have to do this. If you have any better
ideas, please let me know.
"""

from numpy import complex_
from mongoengine import *

class complex_m_(me.Document):

    real = me.FloatField(default=0)
    imag = me.FloatField(default=0)

    def __init__(self, z):
        self.real = z.real
        self.imag = z.imag

    def to_complex(self):
        """convert this to the numpy complex type"""
        return complex_m_(self.real + self.imag * 1j)

    def conjugate(self):
        return complex_m_(self.to_complex().conjugate())

    def __bool__(self):
        return bool(self.to_complex())

    def __neg__(self):
        return complex_m_(self.to_complex().__neg__())

    def __abs__(self):
        return self.to_complex().abs()

    def __eq__(self, other):
        return self.to_complex() == other.to_complex()

    def __ne__(self, other):
        return self.to_complex() != other.to_complex()

    def __add__(self, other):
        return complex_m_(self.to_complex() + other.to_complex())

    def __sub__(self, other):
        return complex_m_(self.to_complex() - other.to_complex())

    def __mul__(self, other):
        return complex_m_(self.to_complex() * other.to_complex())

    def __div__(self, other):
        return complex_m_(self.to_complex() / other.to_complex())

    def __pow__(self, other):
        return complex_m_(self.to_complex() ** other.to_complex())
