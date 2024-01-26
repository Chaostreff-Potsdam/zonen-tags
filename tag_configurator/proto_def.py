"""
c-structures are copies from AP firmware.
used for serial communication.
"""
import ctypes
from enum import Enum, IntEnum

from c_util import c_pretty


class InvalidDataTypeError(Exception):
    def __init__(self, data_type):
        super().__init__("Invalid data type " + str(data_type))


class Colors(tuple, Enum):
    """
    helper for color-palletes
    """

    BLACK = (0x00, 0x00, 0x00)
    RED = (0xFF, 0x00, 0x00)
    WHITE = (0xFF, 0xFF, 0xFF)

    @property
    def index(self):
        indices = {Colors.BLACK: 0, Colors.RED: 1, Colors.WHITE: 2}
        return indices[self]


class DataType(IntEnum):
    """
    enum for the different data-types, which can be transferred to the tag.
    """

    BLACK = 0x20
    BLACK_RED = 0x21
    FIRMWARE_UPDATE = 0x03

    @property
    def color_palette(self):
        """Returns the color palette for the given data type."""
        if self == DataType.BLACK:
            return [*tuple(Colors.BLACK)]
        elif self == DataType.BLACK_RED:
            return [*tuple(Colors.BLACK), *tuple(Colors.RED)]
        else:
            raise InvalidDataTypeError(self)

    @property
    def colors(self):
        """Returns the colors for the given data type."""
        if self == DataType.BLACK:
            return [Colors.BLACK.index]
        elif self == DataType.BLACK_RED:
            return [Colors.BLACK.index, Colors.RED.index]
        else:
            raise InvalidDataTypeError(self)


class EPT_LUT(IntEnum):
    """
    enum for the different LUTs, which can be transferred to the tag.
    """

    DEFAULT = 0
    NO_REPEATS = 1
    FAST_NO_REDS = 2
    FAST = 3


MacAddress = ctypes.c_uint8 * 8
DataVersion = ctypes.c_uint8 * 8

# @c_pretty
# class APInfo(ctypes.Structure):
#     _pack_ = 1
#     _fields_ = (
#         ("hardwareType", ctypes.c_uint8),
#         ("version", DataVersion),  # MD5 (first half) of potential traffic
#         ("dataSize", ctypes.c_uint32),
#         ("dataType", ctypes.c_uint8),  # allows for 16 different datatypes
#         # extra specification or instruction for the tag (LUT to be used for drawing image)
#         ("dataTypeArgument", ctypes.c_uint8),
#         (
#             "nextCheckIn",
#             ctypes.c_uint16,
#         ),  # when should the tag check-in again? Measured in minutes
#         ("attemptsLeft", ctypes.c_uint16),
#         ("targetMac", MacAddress),
#     )

@c_pretty
class AvailableDataRequest(ctypes.Structure):
    _fields_ = (
        ("outerChecksum", ctypes.c_uint8),
        ("sourceMac", MacAddress),
        ("innerChecksum", ctypes.c_uint8),
        ("lastPacketLQI", ctypes.c_uint8),
        ("lastPacketRSSI", ctypes.c_int8),
        ("temperature", ctypes.c_int8),
        ("batteryMv", ctypes.c_uint16),
        ("hwType", ctypes.c_uint8),
        ("wakeupReason", ctypes.c_uint8),
    )


@c_pretty
class AvailDataInfo(ctypes.Structure):
    _pack_ = 1
    _fields_ = (
        ("checksum", ctypes.c_uint8),
        ("dataVer", DataVersion),  # MD5 (first half) of potential traffic
        ("dataSize", ctypes.c_uint32),
        ("dataType", ctypes.c_uint8),  # allows for 16 different datatypes
        # extra specification or instruction for the tag (LUT to be used for drawing image)
        ("dataTypeArgument", ctypes.c_uint8),
        (
            "nextCheckIn",
            ctypes.c_uint16,
        ),  # when should the tag check-in again? Measured in minutes
        ("attemptsLeft", ctypes.c_uint16),
        ("targetMac", MacAddress),
    )

    def update_checksum(self):
        self.checksum = calculate_8bit_checksum(bytes(self))


@c_pretty
class BlockRequest(ctypes.Structure):
    _pack_ = 1
    _fields_ = (
        ("checksum", ctypes.c_uint8),
        ("dataVer", DataVersion),  # MD5 (first half) of potential traffic
        ("blockId", ctypes.c_uint8),
        ("srcMac", MacAddress),
    )


@c_pretty
class BlockHeader(ctypes.Structure):
    _pack_ = 1
    _fields_ = (
        ("length", ctypes.c_uint16),
        ("checksum", ctypes.c_uint16),
    )


@c_pretty
class XferComplete(ctypes.Structure):
    _pack_ = 1
    _fields_ = (
        ("checksum", ctypes.c_uint8),
        ("srcMac", MacAddress),
    )


def calculate_8bit_checksum(data):
    """
    calculates the 8-bit checksum for the given data.
    """
    return sum(data) % 0x100


def calculate_16bit_checksum(data):
    """
    calculates the 16-bit checksum for the given data.
    """
    return sum(data) % 0x10_000
