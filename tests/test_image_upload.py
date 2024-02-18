import logging
from pathlib import Path
from tag_configurator.proto_def import (
    DataType,
)
from tag_configurator import libap


class FakeSerial:
    def __init__(self, *arg, **kwargs):
        with open("tests/serial_log.txt", "r") as fp:
            self.log = fp.readlines()

        self.action = None
        self.expected_data = None
        self.length = None
        self.index = 0
        self.next_line()

    def next_line(self):
        line = self.log.pop(0).split(",")
        self.index += 1
        if line[0] == "read":
            self.action = line[0]
            self.length = int(line[1])
            self.expected_data = bytes.fromhex(line[2])
        else:
            self.action = line[0]
            self.expected_data = bytes.fromhex(line[1])

    def read(self, size=1):
        result = bytearray()
        for i in range(0, size):
            if self.length == 0:
                self.next_line()
                assert self.action == "read", f"line: {self.index}"
            self.length -= 1
            result.append(self.expected_data[0])
            self.expected_data = self.expected_data[1:]
        return bytes(result)

    def write(self, data):
        self.next_line()
        assert self.action == "write", self.index
        assert data == self.expected_data, (
            data.hex() + " != " + self.expected_data.hex() + "in line" + self.index
        )
        # self.next_line()

    def flushInput(self):
        pass


def test_full_upload_stream():
    logging.basicConfig(
        format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
        level=logging.INFO,
    )
    success = [False]

    def get_image(mac, adr):
        if mac == "0000021b1ad03b17":
            return (
                libap.load_image(
                    Path("tests/0000021b1ad03b17.png"), DataType.BLACK_RED
                ),
                DataType.BLACK_RED,
            )
        return None, None

    def upload_successful(ap, mac):
        ap.enabled = False
        success.pop()
        success.append(True)

    access_point = libap.AccessPoint(
        get_image=get_image,
        upload_successful=upload_successful,
        serial_port=FakeSerial(),
    )
    access_point.main_loop()
    assert success.pop(), "Upload failed!"
