# -*- coding: utf-8 -*-
# Run test_umsgpack.py to test the correctness of umsgpack_ext.py:
#
#   $ python3 test_umsgpack_ext.py
#   $ micropython test_umsgpack_ext.py

import unittest
from machine import Pin

import umsgpack
from umsgpack.umsgpack_ext import Complex, Set, Tuple, PinInt, PinStr, PinTuple


def roundtrip (obj, **options):
    return umsgpack.loads(umsgpack.dumps(obj, **options), **options)

class TestUmsgpackExt(unittest.TestCase):

    def test_complex(self):
        obj = complex(1, 2)
        ext = Complex(obj)
        self.assertEqual(str(ext), "Complex((1+2j))")
        self.assertEqual(obj, roundtrip(obj))

    def test_set(self):
        obj = set([1, 2, 3])
        ext = Set(obj)
        self.assertEqual(str(ext), "Set({1, 2, 3})")
        self.assertEqual(obj, roundtrip(obj))

    def test_tuple(self):
        obj = tuple([1, 2, 3])
        ext = Tuple(obj)
        self.assertEqual(str(ext), "Tuple((1, 2, 3))")
        self.assertEqual(obj, roundtrip(obj))

    def test_pin_int(self):
        Pin.TYPE=1
        obj = Pin(0)
        ext = PinInt(obj)
        self.assertEqual(str(ext), "Pin(0)")
        self.assertEqual(obj, roundtrip(obj, pin_id=Pin.TYPE))

    def test_pin_str(self):
        Pin.TYPE=2
        obj = Pin("LED1")
        ext = PinStr(obj)
        self.assertEqual(str(ext), "Pin('LED1')")
        self.assertEqual(obj, roundtrip(obj, pin_id=Pin.TYPE))

    def test_pin_tuple(self):
        Pin.TYPE=3
        obj = Pin(("GPIO_1", 1))
        ext = PinTuple(obj)
        self.assertEqual(str(ext), "Pin(('GPIO_1', 1))")
        self.assertEqual(obj, roundtrip(obj, pin_id=Pin.TYPE))

if __name__ == '__main__':
    unittest.main()
