"""This script uploads an image to the access point."""
#! python3
from enum import Enum, auto
import io
import requests
from PIL import Image
import click


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
    image_path: str,
    display_size: DisplaySize,
    display_mac: str,
    ap_ip: str,
    dither: bool = False,
):
    """Upload an image to the access point."""
    rgb_image = Image.open(image_path)
    rgb_image = rgb_image.convert("RGB")

    if rgb_image.size != display_size.size:
        # pylint: disable=line-too-long
        raise ValueError(
            f"Image size {rgb_image.size} does not match display size {display_size.size} ({display_size.name})."
        )

    payload = {"dither": int(bool(dither)), "mac": expand_mac(display_mac)}
    buffer = io.BytesIO()
    rgb_image.save(buffer, "JPEG", quality="maximum")

    return requests.post(
        build_ap_url(ap_ip), data=payload, files={"file": buffer.getvalue()}, timeout=10
    )


@click.argument("ip")
# @click.argument("mac")
@click.argument("image_path")
@click.option(
    "-s",
    "--display-size",
    type=click.Choice(DisplaySize.__members__),
    callback=lambda c, p, v: getattr(DisplaySize, v) if v else None,
    default="MEDIUM",
)
@click.option("-d", "--dither", is_flag=True, show_default=True, default=False)
@click.command()
def main(image_path, ip, display_size, dither):
    """Upload an image to the access point."""
    while True:
        mac = input("input mac to upload image: ")
        try:
            upload_image(image_path, display_size, mac, ip, dither=dither)
        except ConnectionError:
            print("Could not connect to the access point")


if __name__ == "__main__":
    # pylint: disable=no-value-for-parameter
    main()
