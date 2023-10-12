from enum import Enum, auto
import io
import requests
from PIL import Image, ImageDraw, ImageFont

image = Image.new('P', (296, 128))

palette = [
    255, 255, 255,  # white
    0, 0, 0,        # black
    255, 0, 0       # red
]

# # Assign the color palette to the image
image.putpalette(palette)

# # Initialize the drawing context
draw = ImageDraw.Draw(image)

# # Define the text lines
line1 = "Hallo :)"
# line2 = "und selbst?"

# # line1 = "24"
# # #line1 = ""
# # line2 = ""

# # Define the fonts and sizes
font_line1 = ImageFont.truetype('comic.ttf', size=48)  # Change the font file and size as per your preference
# font_line2 = ImageFont.truetype('comic.ttf', size=36)  # Change the font file and size as per your preference

# # Calculate the text bounding boxes to get the text widths and heights
text_bbox_line1 = draw.textbbox((0, 0), line1, font=font_line1)
# text_bbox_line2 = draw.textbbox((0, 0), line2, font=font_line2)

# # Calculate the text positions to center the lines horizontally
text_position_line1 = ((image.width - (text_bbox_line1[2] - text_bbox_line1[0])) // 2, 15)
# text_position_line2 = ((image.width - (text_bbox_line2[2] - text_bbox_line2[0])) // 2, 55)

# # Write the text on the image
draw.text(text_position_line1, line1, fill=2, font=font_line1)  # Use palette index 1 for black color
# draw.text(text_position_line2, line2, fill=1, font=font_line2)  # Use palette index 2 for red color

# # Convert the image to 24-bit RGB
rgb_image = image.convert('RGB')

# # Save the image as JPEG with maximum quality

rgb_image.save("image.jpg", "JPEG", quality="maximum")
