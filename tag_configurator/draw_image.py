"""This script draws text on an image and saves it as a JPEG file."""
import json

try:
    import tomllib
except ImportError:
    # use tomli as drop in replacement for tomllib
    # only for python<3.11
    import tomli as tomllib
from pathlib import Path

from PIL import Image, ImageDraw, ImageFont

RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

COLORS = [BLACK, RED, WHITE]

FONT_BASE_PATH = "tag_configurator/static/fonts"
ICON_BASE_PATH = Path("tag_configurator/static/icons")


def build_font_path(font_name: str):
    """Build the path to the font file."""
    return f"{FONT_BASE_PATH}/{font_name}"


def calculate_bounding_box(
    draw, font_path: str, font_size: int, text: str
) -> tuple[int, int, tuple[int, int, int, int]]:
    """Calculate the bounding box of the text."""
    font = ImageFont.truetype(str(font_path), size=font_size)
    bounding_box = draw.textbbox((0, 0), text, font=font)
    text_width = bounding_box[2] - bounding_box[0]
    text_height = bounding_box[3] - bounding_box[1]
    return text_width, text_height, bounding_box


def find_optimal_font_size(
    draw, text: str, font_path: str, target_width: int, target_height: int
) -> tuple[int, tuple[int, int, tuple[int, int, int, int]]]:
    """Find the optimal font size for the given text."""
    font_size = 5
    step_size = 1
    text_width = 0
    text_height = 0

    while text_width < target_width and text_height < target_height:
        text_width, text_height, _ = calculate_bounding_box(
            draw, font_path, font_size, text
        )
        font_size += step_size

    font_size -= step_size
    return font_size, calculate_bounding_box(draw, font_path, font_size, text)


def draw_text(
    field_name: str,
    content: str,
    template_json: json,
    draw,
    draw_bbox: bool = False,
    draw_text_area: bool = False,
):
    """Draw the text on the image."""
    if content == "":
        return
    field_settings = template_json[field_name]

    font_path = build_font_path(field_settings["font"])

    top_left = field_settings["top_left"]
    bottom_right = field_settings["bottom_right"]
    margin = field_settings["margin"]
    alignment = field_settings["align"]
    vertical_alignment = field_settings["vertical-align"]

    target_width = bottom_right[0] - top_left[0] - (margin[0] * 2)
    target_height = bottom_right[1] - top_left[1] - (margin[1] * 2)

    if "font-size" in field_settings:
        font_size = field_settings["font-size"]
        text_width, text_height, text_bbox = calculate_bounding_box(
            draw, font_path, font_size, content
        )
    else:
        font_size, (text_width, text_height, text_bbox) = find_optimal_font_size(
            draw, content, font_path, target_width, target_height
        )

    if alignment == "center":
        padding_x = (target_width - text_width) // 2
    elif alignment == "left":
        padding_x = 0
    elif alignment == "right":
        padding_x = target_width - text_width

    if vertical_alignment == "center":
        padding_y = (target_height - text_height) // 2
    elif vertical_alignment == "top":
        padding_y = 0
    elif vertical_alignment == "bottom":
        padding_y = target_height - text_height

    # top left corner of the text
    text_position_without_offset = (
        top_left[0] + padding_x + margin[0],
        top_left[1] + padding_y + margin[1],
    )

    text_position_with_offset = (
        text_position_without_offset[0] - text_bbox[0],
        text_position_without_offset[1] - text_bbox[1],
    )
    if draw_text_area:
        draw.rectangle((*top_left, *bottom_right), fill=WHITE)

    draw.text(
        text_position_with_offset,
        content,
        fill=tuple(field_settings["color"]),
        font=ImageFont.truetype(font_path, size=font_size),
    )
    if draw_bbox:
        draw.rectangle(
            (
                *text_position_without_offset,
                text_position_without_offset[0] + text_bbox[2],
                text_position_without_offset[1] + text_bbox[3] - text_bbox[1],
            ),
            outline=BLACK,
        )


def draw_image(field_name, content, template_json, image):
    """Draw the image on the image."""
    image_settings = template_json[field_name]
    icon_path = ICON_BASE_PATH / content
    icon = Image.open(str(icon_path))
    image.alpha_composite(icon, tuple(image_settings["top_left"]))


def generate_image(
    args: dict[str, dict],
    template_image_path: str,
    output_path: str,
    draw_bbox: bool = False,
    draw_text_area: bool = False,
):
    """Generate the image with the given name and pronouns."""
    template_image_path = Path(template_image_path)
    template_json_path = template_image_path.with_suffix(".toml")

    image = Image.open(template_image_path).convert("RGBA")

    with open(template_json_path, "rb") as template_json_file:
        template_json = tomllib.load(template_json_file)

    draw = ImageDraw.Draw(image)
    draw.fontmode = "1"  # no anti-aliasing

    for field_name, content in args.items():
        if template_json[field_name]["type"] == "text":
            draw_text(
                field_name, content, template_json, draw, draw_bbox, draw_text_area
            )
        elif template_json[field_name]["type"] == "image":
            draw_image(field_name, content, template_json, image)

    # Convert the image to 24-bit RGB
    rgb_image = image.convert("RGB")

    if output_path is not None:
        Path(output_path).parent.mkdir(parents=True, exist_ok=True)
        # Save the image as JPEG with maximum quality
        rgb_image.save(output_path, "JPEG", quality="maximum")

    return rgb_image
