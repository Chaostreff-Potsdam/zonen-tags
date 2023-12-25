#! python3
"""This script uploads an image to the access point."""
import io
from enum import Enum, auto

import click
import requests
from PIL import Image


class DisplaySize(Enum):
    """Enum for the display sizes."""

    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    EXTRA_LARGE = auto()

    @property
    def size(self) -> tuple[int, int]:
        """Get the size of the display (width, height)."""
        _sizes_map = {
            DisplaySize.SMALL: (152, 152),
            DisplaySize.MEDIUM: (296, 128),
            DisplaySize.LARGE: (400, 300),
            DisplaySize.EXTRA_LARGE: (640, 384),
        }
        return _sizes_map[self]


def build_ap_url(ap_ip: str):
    """Build the url to the access point."""
    return f"http://{ap_ip}/imgupload"


def expand_mac(mac: str):
    """Expand the mac address to the format used by the access point."""
    return mac.zfill(16).upper()


def upload_image(
    image: str,
    display_mac: str,
    ap_ip: str,
    dither: bool = False,
):
    """Upload an image to the access point."""
    rgb_image = image.convert("RGB")

    if rgb_image.size not in {size.size for size in DisplaySize}:
        # pylint: disable=line-too-long
        raise ValueError(
            f"Image size {rgb_image.size} does not match any display size."
        )

    payload = {"dither": int(bool(dither)), "mac": expand_mac(display_mac)}
    buffer = io.BytesIO()
    rgb_image.save(buffer, "JPEG", quality="maximum")

    return requests.post(
        build_ap_url(ap_ip), data=payload, files={"file": buffer.getvalue()}, timeout=10
    )


def upload_image_from_path(
    image_path: str,
    display_mac: str,
    ap_ip: str,
    dither: bool = False,
):
    """Open the image and upload it to the access point."""
    return upload_image(Image.open(image_path), display_mac, ap_ip, dither=dither)


@click.argument("image_path")
@click.argument("mac")
@click.argument("ip")
@click.option("-d", "--dither", is_flag=True, show_default=True, default=False)
@click.command()
def main(ip, mac, image_path, dither):
    """Upload an image to the access point."""
    # while True:
    # mac = input("input mac to upload image: ")
    try:
        response = upload_image_from_path(image_path, mac, ip, dither=dither)
        print(response.content.decode("utf-8"))
    except ConnectionError:
        print("Could not connect to the access point")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
