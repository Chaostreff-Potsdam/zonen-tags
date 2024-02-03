#! python3
"""This script uploads new firmware to a tag."""

import logging
import click
from tag_configurator.libap import AccessPoint, load_firmware
from tag_configurator.proto_def import DataType
from tag_configurator.upload_image import expand_mac


def upload_firmware_via_station(
    firmware_path: str,
    display_mac: str,
    port: str
):
    """Upload an image to the access point."""
    firmware = load_firmware(firmware_path)
    loop = len(display_mac) == 0
    expanded_macs = [expand_mac(mac) for mac in display_mac]

    def get_image(mac):
        if loop or expand_mac(mac) in expanded_macs:
            return firmware, DataType.FIRMWARE_UPDATE
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
@click.argument("firmware_path")
@click.option(
    "-p",
    "--port",
    show_default=True,
    default="/dev/ttyACM0",
    help="The Zigbee Sticks serial port",
)
@click.option("-v", "--verbose", is_flag=True, show_default=True, default=False)
@click.command()
def main(firmware_path, mac, port, verbose):
    """Upload an image to the access point."""
    logging.basicConfig(
        format="%(asctime)s - %(name)s - [%(levelname)s] - %(message)s",
        level=logging.DEBUG if verbose else logging.INFO,
    )
    upload_firmware_via_station(firmware_path, mac, port)


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
