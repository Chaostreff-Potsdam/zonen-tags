import ctypes
import hashlib
import logging
from collections import deque
from pathlib import Path
from time import sleep

import serial
from bitarray import bitarray
from PIL import Image

from c_util import hex_bytes, hex_reverse_bytes
from proto_def import (
    EPT_LUT,
    AvailableDataRequest,
    AvailDataInfo,
    BlockHeader,
    BlockRequest,
    Colors,
    DataType,
    XferComplete,
    calculate_8bit_checksum,
    calculate_16bit_checksum,
)

BLOCK_SIZE = 4096


def load_image(image_path: Path, data_type: DataType):
    image = Image.open(image_path)
    return image2tag_format(image, data_type)


def quantize_image(image: Image, color_palette: list):
    """Quantize the image to the given color palette."""
    palette_image = Image.new("P", (1, 1))
    palette_image.putpalette(
        color_palette + [*tuple(Colors.WHITE)] * (256 - len(color_palette))
    )
    return image.quantize(palette=palette_image, dither=Image.Dither.NONE)


def image2tag_format(image: Image, data_type: DataType):
    """Convert a PIL RGB image to the bit-format used by the tag.

    the tag picture format is:
        - one full frame per color
        - each frame consist of $height columns of $with pixels
        Note: so the image is rotated by 90-deg
        - each column (line from src image) is transferred in reverse
        - each pixel is one bit (the epaper only knows "WHITE" (0) or "COLOR" (1))
    due to the below algorithm, all colors, except for exact matches of the defined
    colors, are ignored (remain white)
    """
    image = image.convert("RGB")
    width, height = image.size
    pixel_colors = bitarray()

    quantized_image = quantize_image(image, color_palette=data_type.color_palette)

    # one frame per color
    for color in data_type.colors:
        # transfer lines (columns in output) in reverse
        for x in reversed(range(width)):
            for y in range(height):
                # each pixel is on bit (True or False)
                pixel_colors.append(quantized_image.getpixel((x, y)) == color)
    # bitarray handles packing of 8-booleans to one byte
    return pixel_colors.tobytes()


def xor(data):
    return bytes(b ^ 0xAA for b in data)


def short_md5(data):
    """Computes the first 8 bytes of the MD5 hash of the given data.

    # the tag and AP firmware uses a 64-bit "version" to check, whether
    # it has an up-to date image. we currently just use half of a MD5-hash
    # of a picture to generate a new value, if the picture data changes.
    """

    return (ctypes.c_ubyte * 8).from_buffer_copy(hashlib.md5(data).digest()[:8])


class AccessPoint:
    def __init__(
        self,
        get_image: callable,
        upload_successful: callable,
        serial_port: str = "/dev/ttyACM0",
    ):
        self.log = logging.getLogger("AccessPoint")

        self.ap = serial.Serial(serial_port, 115200, timeout=0.1)
        self.ap.flushInput()
        self.get_image = get_image
        self.upload_successful = upload_successful
        self.enabled = True

    def read_hex(self, length):
        return bytes.fromhex(self.ap.read(length * 2).decode("utf-8"))

    def wait4str(self, string):
        if isinstance(string, str):
            string = string.encode("utf-8")
        input_buffer = deque(maxlen=len(string))
        while True:
            input_buffer.append(self.ap.read())
            command = b"".join(input_buffer)
            if command == string:
                return True

    def wait_and_read(self, start_string, length, end_string="\n"):
        self.wait4str(start_string)
        result = self.read_hex(length)
        self.wait4str(end_string)
        return result

    def main_loop(self):
        self.enabled = True
        input_buffer = deque(maxlen=4)
        while self.enabled:
            input_buffer.append(self.ap.read())
            command = b"".join(input_buffer)
            if command == b"ADR>":
                self.handle_available_data_request()
            elif command == b"RQB>":
                self.handle_block_request()
            elif command == b"XFC>":
                self.handle_transfer_complete()
            elif command == b"ACK>":
                self.handle_ack()

    def get_ap_info(self):
        """Reads the AP info and prints it to the log."""
        self.ap.write(b"NFO?")
        self.wait4str("ACK>")

        hw_type = int.from_bytes(self.wait_and_read("TYP>", 1))
        version = int.from_bytes(self.wait_and_read("VER>", 2))
        mac = self.wait_and_read("MAC>", 8)
        channel = int.from_bytes(self.wait_and_read("ZCH>", 1))
        power = int.from_bytes(self.wait_and_read("ZPW>", 1))
        pending = int.from_bytes(self.wait_and_read("PEN>", 1))
        no_update = int.from_bytes(self.wait_and_read("NOP>", 1))

        self.log.info(f"AP MAC: {hex_reverse_bytes(mac)}")
        self.log.info(f"HW Type: {hw_type}, Version: {version}, Power: {power}")
        self.log.info(f"Channel: {channel}, Pending: {pending}, No Update: {no_update}")

        return {
            "hw_type": hw_type,
            "version": version,
            "mac": mac,
            "channel": channel,
            "power": power,
            "pending": pending,
            "no_update": no_update,
        }

    def handle_available_data_request(self):
        """
        handles an AvailableDataRequest, which is issued by the AP
        whenever a tag checks-in with the AP. The tag provides some
        useful data - which we store.
        we then check, if there is new data available for the tag -
        hence the method name. if so, we generate an AvailDataInfo,
        which the AP will deliver to the tag on its next check-in
        """

        buffer = self.ap.read(30)  # ctypes.sizeof(AvailableDataRequest))
        adr = AvailableDataRequest.from_buffer_copy(buffer)

        pretty_mac = hex_reverse_bytes(adr.sourceMac)
        self.log.info(f"Check-in from MAC {pretty_mac}")
        self.log.debug(f"{adr}")

        mac = hex_reverse_bytes(adr.sourceMac, None)

        image, data_type = self.get_image(mac)

        if image is None:
            self.log.info(f"No image found for {pretty_mac}")
            return

        sda = AvailDataInfo(
            checksum=0,
            dataVer=short_md5(image),
            dataSize=len(image),
            dataType=int(data_type),
            dataTypeArgument=int(EPT_LUT.NO_REPEATS),
            nextCheckIn=0,  # default taken from ESP firmware
            attemptsLeft=60 * 24,  # default taken from ESP firmware
            targetMac=adr.sourceMac,
        )
        sda.update_checksum()

        self.log.info(f"Tag needs new data. sending {sda}")
        self.log.info(bytes(sda).hex(" "))

        self.ap.write(b"SDA>")
        self.ap.write(bytes(sda))

    def handle_block_request(self):
        """
        Handles a BlockRequest, which is issued by the AP when it needs data
        to transfer to a tag. data is split-up into blocks of 4096 bytes, prefixed
        with a header and sent with a special encoding (XORd with 0xAA) - only god
        knows why, as this only makes sense, if the receiver can recover timing info
        from the signal (maybe?)
        """
        buffer = self.ap.read(ctypes.sizeof(BlockRequest))
        block_request = BlockRequest.from_buffer_copy(buffer)

        self.log.debug(f"{block_request}")
        self.log.info(f"Got RQB for MAC {hex_reverse_bytes(block_request.srcMac)}")
        mac = hex_reverse_bytes(block_request.srcMac, None)

        image, data_type = self.get_image(mac)

        if image is None:
            self.log.warning(
                f"No image found for {hex_reverse_bytes(block_request.srcMac)}"
            )
            self.log.info("Sending: cancel block request")
            cxd = AvailDataInfo(targetMac=block_request.srcMac)
            cxd.update_checksum()
            self.ap.write(b"CXD>")
            self.ap.write(bytes(cxd))
            return

        # we just assume, that the data is black-and-red (0x21) - see handle_adr()
        offset = block_request.blockId * BLOCK_SIZE
        length = min(len(image) - offset, BLOCK_SIZE)
        self.log.info(f"Transmitting block {block_request.blockId} of length {length}")

        transmit_data = image[offset : offset + length]
        self.log.debug(f"Block bytes: {transmit_data.hex()}")
        header = bytes(
            BlockHeader(length=length, checksum=calculate_16bit_checksum(transmit_data))
        )
        self.ap.write(b">D>")
        # waiting for a little bit, but not too long, seems to be required for successful transmission.
        # this may be due to the fact, that serial-command processing and the below bulk-transfer are
        # separate processes, as the below bulk-transfer is implemented as a kind of interrupt-driven DMA
        # in the AP.
        sleep(0.05)
        # the AP-firmware XORs the data back on retrieval
        self.ap.write(xor(header))
        self.ap.write(xor(transmit_data))
        # the AP-firmware expects bulk-transfers to always be 4100 bytes (due to the DMA mechanism)
        # thus we need to fill the block with junk (0xFF when unXORd in this case)
        self.ap.write(bytes([0xAA] * (BLOCK_SIZE - length)))

    def handle_transfer_complete(self):
        """
        handles a XFC (transfer-complete) message, which is issued by the AP,
        when it "knows" that a tag has fully received the data, announced by a previous
        AvailDataInfo. this may happen without any actual data-transfer - e.g. if the
        tag has fetched the data from EPROM
        """
        buffer = self.ap.read(ctypes.sizeof(XferComplete))
        xfer_request = XferComplete.from_buffer_copy(buffer)

        pretty_mac = hex_reverse_bytes(xfer_request.srcMac)
        mac = hex_reverse_bytes(xfer_request.srcMac, None)
        self.log.info(f"Got XFC for Mac {pretty_mac}")
        self.upload_successful(self, mac)

    def handle_ack(self):
        self.log.debug("ACK")


if __name__ == "__main__":
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )

    def get_image(mac):
        if mac == "0000021b1ad03b17":
            return (
                load_image(Path("cache/0000021b1ad03b17.png"), DataType.BLACK_RED),
                DataType.BLACK_RED,
            )
        return None, None

    def upload_successful(ap, mac):
        print(f"Upload successful for {mac}")
        ap.enabled = False

    access_point = AccessPoint(get_image=get_image, upload_successful=upload_successful)
    access_point.get_ap_info()
    access_point.main_loop()
