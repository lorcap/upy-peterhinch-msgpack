# umsgpack_ext.py Demo of extending MessagePack to support additional Python
# built-in types.

# Copyright (c) 2021 Peter Hinch Released under the MIT License see LICENSE.

# Each supported type has a class defined with the umsgpack.ext_serializable
# decorator and assigned a unique integer in range 0-127. I arbitrarily chose
# a range starting at 0x50.
# The mpext method accepts an instance of a supported class and returns an
# instance of the appropriate ext_serializable class.

import umsgpack
import struct

try:
    import datetime
except ImportError:
    pass

# Entries in mpext are required where types are to be handled without declaring
# an ext_serializable class in the application. This example enables complex,
# tuple and set types to be packed as if they were native to umsgpack.
# Options (kwargs to dump and dumps) may be passed to constructor including new
# type-specific options
def mpext(obj, options):
    if "datetime" in options and options["datetime"] and isinstance(obj, datetime.datetime):
        return Timestamp.from_datetime(obj)
    if isinstance(obj, complex):
        return Complex(obj)
    if isinstance(obj, set):
        return Set(obj)
    if isinstance(obj, tuple):
        return Tuple(obj)
    return obj

@umsgpack.ext_serializable(-1)
class Timestamp:
    def __init__(self, seconds, nanoseconds=0):
        if not (0 <= nanoseconds < 10**9):
            raise ValueError
        self.s = seconds
        self.ns = nanoseconds

    def __str__(self):
        return "Timestamp({}, {})".format(self.s, self.ns)

    def __eq__(self, other):
        return self.s == other.s and self.ns == other.ns

    def __ne__(self, other):
        return not self.__eq__(other)

    def packb(self):
        return self.to_bytes()

    @staticmethod
    def unpackb(data, options):
        ts = Timestamp.from_bytes(data)
        if "timestamp" in options:
            optts = options["timestamp"]
            if optts == 1:
                return ts.to_unix()
            elif optts == 2:
                return ts.to_unix_nano()
            elif optts == 3:
                return ts.to_datetime()
        return ts

    def to_bytes(self):
        if (self.s >> 34) == 0:
            data64 = self.ns << 34 | self.s
            if data64 & 0xFFFFFFFF00000000 == 0:
                data = struct.pack("!L", data64)
            else:
                data = struct.pack("!Q", data64)
        else:
            data = struct.pack("!Iq", self.ns, self.s)
        return data

    @staticmethod
    def from_bytes(b):
        l = len(b)
        if l == 4:
            s = struct.unpack("!L", b)[0]
            ns = 0
        elif l == 8:
            data64 = struct.unpack("!Q", b)[0]
            s = data64 & 0x3FFFFFFFF
            ns = data64 >> 34
        elif l == 12:
            ns, s = struct.unpack("!Iq", b)
        else:
            raise ValueError
        return Timestamp(s, ns)

    def to_unix(self):
        return self.s + self.ns / 1e9

    @staticmethod
    def from_unix(unix_sec):
        s = int(unix_sec // 1)
        ns = int((unix_sec % 1) * 10**9)
        return Timestamp(s, ns)

    def to_unix_nano(self):
        return self.s * 10**9 + self.ns

    @staticmethod
    def from_unix_nano(ns):
        return Timestamp(*divmod(ns, 10**9))

    def to_datetime(self):
        dt = datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        dt += datetime.timedelta(seconds=self.s, nanoseconds=self.ns)
        return dt

    @staticmethod
    def from_datetime(dt):
        dtu = dt.astimezone(datetime.timezone.utc)
        d = dtu - datetime.datetime(1970, 1, 1, tzinfo=datetime.timezone.utc)
        return Timestamp.from_unix_nano(d.nanoseconds)


@umsgpack.ext_serializable(0x50)
class Complex:
    def __init__(self, c):
        self.c = c

    def __str__(self):
        return "Complex({})".format(self.c)

    def packb(self):
        return struct.pack(">ff", self.c.real, self.c.imag)

    @staticmethod
    def unpackb(data, options):
        return complex(*struct.unpack(">ff", data))

@umsgpack.ext_serializable(0x51)
class Set:
    def __init__(self, s):
        self.s = s

    def __str__(self):
        return "Set({})".format(self.s)

    def packb(self):  # Must change to list otherwise get infinite recursion
        return umsgpack.dumps(list(self.s))

    @staticmethod
    def unpackb(data, options):
        return set(umsgpack.loads(data))

@umsgpack.ext_serializable(0x52)
class Tuple:
    def __init__(self, s):
        self.s = s

    def __str__(self):
        return "Tuple({})".format(self.s)

    def packb(self):
        return umsgpack.dumps(list(self.s))  # Infinite recursion

    @staticmethod
    def unpackb(data, options):
        return tuple(umsgpack.loads(data))
