"""This script draws text on an image and saves it as a JPEG file."""
import json
from pathlib import Path
from PIL import Image, ImageDraw, ImageFont

RED = (255, 0, 0)
WHITE = (255, 255, 255)
BLACK = (0, 0, 0)

FONT_BASE_PATH = "tag_configurator/static/fonts"


def build_font_path(font_name: str):
    """Build the path to the font file."""
    return f"{FONT_BASE_PATH}/{font_name}.ttf"


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


def generate_image(
    name: str,
    template_image_path: str,
    output_path: str,
    draw_bbox: bool = False,
    draw_text_area: bool = False,
):
    """Generate the image with the given name and pronouns."""
    template_image_path = Path(template_image_path)
    template_json_path = template_image_path.with_suffix(".json")

    image = Image.open(template_image_path)

    with open(template_json_path, encoding="utf-8") as template_json_file:
        template_json = json.load(template_json_file)

    font_path = build_font_path(template_json["font"])

    draw = ImageDraw.Draw(image)

    top_left = template_json["top_left"]
    bottom_right = template_json["bottom_right"]
    margin = template_json["margin"]

    target_width = bottom_right[0] - top_left[0] - margin[0]
    target_height = bottom_right[1] - top_left[1] - margin[1]

    font_size, (text_width, text_height, text_bbox) = find_optimal_font_size(
        draw, name, font_path, target_width, target_height
    )

    padding_x = (target_width - text_width) // 2
    padding_y = (target_height - text_height) // 2

    # top left corner of the text
    text_position_without_offset = (
        top_left[0] + padding_x,
        top_left[1] + padding_y,
    )
    text_position_with_offset = (
        text_position_without_offset[0] - text_bbox[0],
        text_position_without_offset[1] - text_bbox[1],
    )
    if draw_text_area:
        draw.rectangle((*top_left, *bottom_right), fill=RED)

    draw.text(
        text_position_with_offset,
        name,
        fill=BLACK,
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

    # Convert the image to 24-bit RGB
    rgb_image = image.convert("RGB")
    # Save the image as JPEG with maximum quality
    rgb_image.save(output_path, "JPEG", quality="maximum")
