#! python3
"""This script uploads new firmware to a tag."""

import hashlib
import logging
import click
from .libap import AccessPoint, load_firmware
from .proto_def import DataType
from .upload_image import expand_mac
import requests
from pathlib import Path


def get_firmware_type(firmware_path: str) -> DataType:
    """Get the type of the firmware."""
    firmware_path = Path(firmware_path)
    firmware_name = firmware_path.name
    return "_".join(firmware_name.split("_")[:-1])


def get_firmware_versions():
    url = "https://raw.githubusercontent.com/jjwbruijn/OpenEPaperLink/master/binaries/Tag/tagotaversions.json"
    ota_versions = requests.get(url).json()
    return ota_versions[0]


def get_firmware4type(firmware_entry):
    base_url = (
        "https://raw.githubusercontent.com/jjwbruijn/OpenEPaperLink/master/binaries/Tag"
    )
    url = f"{base_url}/{firmware_entry['type']}_{firmware_entry['version']}.bin"
    binary = requests.get(url).content
    checksum = hashlib.md5(binary).hexdigest()
    if checksum != firmware_entry["md5"]:
        raise ValueError(
            f"Checksum mismatch for {url}. Expected {firmware_entry['md5']}, got {checksum}."
        )
    return binary


def upload_firmware_via_station(
    firmware_path: str, display_mac: str, port: str, ignore_type_check: bool = False
):
    """Upload an image to the access point."""
    firmware_versions = get_firmware_versions()

    loop = len(display_mac) == 0
    expanded_macs = [expand_mac(mac) for mac in display_mac]

    if firmware_path is not None:
        firmware = load_firmware(firmware_path)
        firmware_type = get_firmware_type(firmware_path)
    else:
        # TODO: download/cache all firmares to /tmp or somewhere
        raise NotImplementedError("Firmware download not implemented yet.")
        return

    def get_image(mac, adr):
        if loop or expand_mac(mac) in expanded_macs:
            firmware_entry = firmware_versions[hex(adr.hwType)[2:].zfill(2).upper()]
            hardware_type = firmware_entry["type"]

            if firmware_path is None:
                logging.warning("No firmware path provided.")
                return None, None
                # TODO cross check type with mac address
                # TODO load firmware from local fs cache
                return get_firmware4type(firmware_entry), DataType.FIRMWARE_UPDATE

            if hardware_type == firmware_type or ignore_type_check:
                return firmware, DataType.FIRMWARE_UPDATE
            else:
                logging.warning(
                    f"Skipping {mac} because it is a different hardware type. Expected {firmware_type}, got {hardware_type}."
                )
                return None, None
        return None, None

    def upload_successful(ap, mac):
        logging.info(f"Upload successful for {mac}")
        if loop:
            ap.enabled = True
        else:
            expanded_macs.remove(expand_mac(mac))
            ap.enabled = len(expanded_macs) > 0

    access_point = AccessPoint(
        get_image=get_image, upload_successful=upload_successful, serial_port=port
    )
    access_point.main_loop()


@click.argument("mac", nargs=-1)
@click.option("-f", "--firmware", help="The path to the firmware file.")
@click.option(
    "-p",
    "--port",
    show_default=True,
    default="/dev/ttyACM0",
    help="The Zigbee Sticks serial port",
)
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False)
@click.option(
    "-i", "--ignore-type-check", is_flag=True, show_default=True, default=False
)
@click.command()
def main(firmware, mac, port, verbose, ignore_type_check):
    """Upload an image to the access point."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )
    upload_firmware_via_station(
        firmware, mac, port, ignore_type_check=ignore_type_check
    )


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
