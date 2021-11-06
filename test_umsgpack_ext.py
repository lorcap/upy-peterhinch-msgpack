# -*- coding: utf-8 -*-
# Run test_umsgpack.py to test the correctness of umsgpack_ext.py:
#
#   $ python3 test_umsgpack_ext.py
#   $ micropython test_umsgpack_ext.py
#
# Micropython's datetime.py is need even for Python as to run this tests
# successfully.

import datetime
import unittest

import umsgpack
from umsgpack.umsgpack_ext import Timestamp, Complex, Set, Tuple


class TestUmsgpackExtTimestamp(unittest.TestCase):

    def test_timestamp32(self):
        s = 2 ** 32 - 1
        ts = Timestamp(s)
        self.assertEqual(ts.to_bytes(), b"\xff\xff\xff\xff")
        packed = umsgpack.dumps(ts)
        self.assertEqual(packed, b"\xd6\xff" + ts.to_bytes())
        unpacked = umsgpack.loads(packed)
        self.assertEqual(ts, unpacked)

    def test_timestamp64(self):
        s = 2 ** 34 - 1
        ns = 999999999
        ts = Timestamp(s, ns)
        self.assertEqual(ts.to_bytes(), b"\xee\x6b\x27\xff\xff\xff\xff\xff")
        packed = umsgpack.dumps(ts)
        self.assertEqual(packed, b"\xd7\xff" + ts.to_bytes())
        unpacked = umsgpack.loads(packed)
        self.assertEqual(ts, unpacked)

    def test_timestamp96(self):
        s = 2 ** 63 - 1
        ns = 999999999
        ts = Timestamp(s, ns)
        self.assertEqual(ts.to_bytes(), b"\x3b\x9a\xc9\xff\x7f\xff\xff\xff\xff\xff\xff\xff")
        packed = umsgpack.dumps(ts)
        self.assertEqual(packed, b"\xc7\x0c\xff" + ts.to_bytes())
        unpacked = umsgpack.loads(packed)
        self.assertEqual(ts, unpacked)

    def test_timestamp_neg(self):
        ts = Timestamp.from_unix(-2.3)
        self.assertEqual(ts.s, -3)
        self.assertEqual(ts.ns, 700000000)
        self.assertEqual(ts.to_bytes(), b"\x29\xb9\x27\x00\xff\xff\xff\xff\xff\xff\xff\xfd")
        packed = umsgpack.dumps(ts)
        self.assertEqual(packed, b"\xc7\x0c\xff" + ts.to_bytes())
        unpacked = umsgpack.loads(packed)
        self.assertEqual(ts, unpacked)


class TestUmsgpackExtTimestampUnpack(unittest.TestCase):

    def test_timestamp32(self):
        self.assertEqual(umsgpack.loads(b"\xd6\xff\x00\x00\x00\x00"), Timestamp(0))

    def test_timestamp64(self):
        self.assertEqual(umsgpack.loads(b"\xd7\xff" + b"\x00" * 8), Timestamp(0))
        with self.assertRaises(ValueError):
            umsgpack.loads(b"\xd7\xff" + b"\xff" * 8)

    def test_timestamp96(self):
        self.assertEqual(umsgpack.loads(b"\xc7\x0c\xff" + b"\x00" * 12), Timestamp(0))
        with self.assertRaises(ValueError):
            umsgpack.loads(b"\xc7\x0c\xff" + b"\xff" * 12) == Timestamp(0)

    def test_undefined(self):
        with self.assertRaises(ValueError):
            umsgpack.loads(b"\xd4\xff\x00")
        with self.assertRaises(ValueError):
            umsgpack.loads(b"\xd5\xff\x00\x00")
        with self.assertRaises(ValueError):
            umsgpack.loads(b"\xc7\x00\xff")
        with self.assertRaises(ValueError):
            umsgpack.loads(b"\xc7\x03\xff\0\0\0")
        with self.assertRaises(ValueError):
            umsgpack.loads(b"\xc7\x05\xff\0\0\0\0\0")


class TestUmsgpackExtTimestampUnix(unittest.TestCase):

    def test_timestamp_from(self):
        t = Timestamp(42, 14000)
        self.assertEqual(Timestamp.from_unix(42.000014), t)
        self.assertEqual(Timestamp.from_unix_nano(42000014000), t)

    def test_timestamp_to(self):
        t = Timestamp(42, 14000)
        self.assertEqual(t.to_unix(), 42.000014)
        self.assertEqual(t.to_unix_nano(), 42000014000)


_utc = datetime.timezone.utc

class TestUmsgpackExtTimestampDatetime(unittest.TestCase):

    def test_timestamp_datetime(self):
        t = Timestamp(42, 14)
        self.assertEqual(t.to_datetime(), datetime.datetime(1970, 1, 1, 0, 0, 42, 14, _utc))

    def test_unpack_datetime(self):
        t = Timestamp(42, 14)
        packed = umsgpack.dumps(t)
        unpacked = umsgpack.loads(packed, timestamp=3)
        self.assertEqual(unpacked, datetime.datetime(1970, 1, 1, 0, 0, 42, 14, _utc))

    def test_pack_unpack_before_epoch(self):
        t_in = datetime.datetime(1960, 1, 1, tzinfo=_utc)
        packed = umsgpack.dumps(t_in, datetime=True)
        unpacked = umsgpack.loads(packed, timestamp=3)
        self.assertEqual(unpacked, t_in)

    def test_pack_datetime(self):
        t = Timestamp(42, 14000)
        dt = t.to_datetime()
        self.assertEqual(dt, datetime.datetime(1970, 1, 1, 0, 0, 42, 14000, _utc))

        packed = umsgpack.dumps(dt, datetime=True)
        packed2 = umsgpack.dumps(t)
        self.assertEqual(packed, packed2)

        unpacked = umsgpack.loads(packed)
        self.assertEqual(unpacked, t)

        unpacked = umsgpack.loads(packed, timestamp=3)
        self.assertEqual(unpacked, dt)

    def test_msgpack_issue451(self):
        dt = datetime.datetime(2100, 1, 1, 1, 1, tzinfo=_utc)
        packed = umsgpack.dumps(dt, datetime=True)
        self.assertEqual(packed, b"\xd6\xff\xf4\x86eL")

        unpacked = umsgpack.loads(packed, timestamp=3)
        self.assertEqual(dt, unpacked)


def roundtrip (obj):
    return umsgpack.loads(umsgpack.dumps(obj))

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


if __name__ == '__main__':
    unittest.main()
