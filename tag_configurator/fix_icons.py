#! python3
"""Fix the icons in the tag configurator."""
import click
from PIL import Image

RED = (255, 0, 0, 255)
WHITE = (255, 255, 255, 255)
BLACK = (0, 0, 0, 0)

COLORS = [BLACK, RED, WHITE]


def get_pixel_difference(
    pixel1: tuple[int, int, int, int], pixel2: tuple[int, int, int, int]
):
    """Get the difference between two RGBA pixels."""
    return sum((abs(pixel1[i] - pixel2[i]) for i in range(4)))


def find_closest_color(
    pixel: tuple[int, int, int, int], colors: list[tuple[int, int, int, int]]
):
    """Find the closest color to the given pixel."""
    min_diff = 1000
    closest_color = None
    for color in colors:
        diff = get_pixel_difference(pixel, color)
        if diff < min_diff:
            min_diff = diff
            closest_color = color
    return closest_color


def fix_image(img: Image, colors: list[tuple[int, int, int, int]]):
    """Fix the image by quantizing the colors."""
    for index, pixel in enumerate(img.getdata()):
        if pixel not in colors:
            img.putpixel(
                (index % img.width, index // img.width),
                find_closest_color(pixel, colors),
            )

    return img


@click.argument("input_path")
@click.command()
def main(input_path):
    """Fix the image given as INPUT_PATH.
    Quantize the colors in the image to the list of allowed colors.
    Convert black pixels to transparent pixels.
    """
    fix_image(
        Image.open(input_path).convert("RGBA"),
        COLORS,
    ).save(input_path)


if __name__ == "__main__":
    main()
