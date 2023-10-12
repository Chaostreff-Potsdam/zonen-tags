from enum import Enum, auto
import io
import requests
from PIL import Image, ImageDraw, ImageFont

class DisplaySize(Enum):
    SMALL = auto()
    MEDIUM = auto()
    LARGE = auto()
    EXTRA_LARGE = auto()

    @property
    def size(self):
        _sizes_map = {
            DisplaySize.SMALL: (152, 152),
            DisplaySize.MEDIUM: (296, 128),
            DisplaySize.LARGE: (400, 300),
            DisplaySize.EXTRA_LARGE: (640, 384),
        }
        return _sizes_map[self]

mac = "0000021F818E3B1A"   # destination mac address
mac = "0000021ae972341d"   # destination mac address
mac = "00000219fecb3b15"
mac = "000002B336853414" # mittel
mac = "0000021E7034743D" # groß
dither = 1   # set dither to 1 is you're sending photos etc
apip = "192.168.178.237"   # ip address of your access point


# # Create a new paletted image with indexed colors
# image = Image.new('P', (296, 128))

# # image = Image.new('P', (152,152))

# # Define the color palette (white, black, red)
# palette = [
#     255, 255, 255,  # white
#     0, 0, 0,        # black
#     255, 0, 0       # red
# ]

# # Assign the color palette to the image
# image.putpalette(palette)

# # Initialize the drawing context
# draw = ImageDraw.Draw(image)

# # Define the text lines
# line1 = "Gut"
# line2 = "und selbst?"

# # line1 = "24"
# # #line1 = ""
# # line2 = ""

# # Define the fonts and sizes
# font_line1 = ImageFont.truetype('comic.ttf', size=36)  # Change the font file and size as per your preference
# font_line2 = ImageFont.truetype('comic.ttf', size=36)  # Change the font file and size as per your preference

# # Calculate the text bounding boxes to get the text widths and heights
# text_bbox_line1 = draw.textbbox((0, 0), line1, font=font_line1)
# text_bbox_line2 = draw.textbbox((0, 0), line2, font=font_line2)

# # Calculate the text positions to center the lines horizontally
# text_position_line1 = ((image.width - (text_bbox_line1[2] - text_bbox_line1[0])) // 2, 15)
# text_position_line2 = ((image.width - (text_bbox_line2[2] - text_bbox_line2[0])) // 2, 55)

# # Write the text on the image
# draw.text(text_position_line1, line1, fill=2, font=font_line1)  # Use palette index 1 for black color
# draw.text(text_position_line2, line2, fill=1, font=font_line2)  # Use palette index 2 for red color

# # Convert the image to 24-bit RGB
# rgb_image = image.convert('RGB')

# # Save the image as JPEG with maximum quality

# Image.open("/home/felix/Downloads/geekend.gray600x300.jpg")

def upload_image(image_path:str, display_size: DisplaySize, display_mac:str, ap_url:str, dither=False):
    rgb_image = Image.open(image_path)
    rgb_image = rgb_image.convert("RGB")
    rgb_image = rgb_image.resize(display_size.size)
    buffer = io.BytesIO()
    rgb_image.save(buffer, "JPEG", quality="maximum")
    rgb_image.save("testing.jpg", "JPEG", quality="maximum")
    url = "http://" + ap_url + "/imgupload"
    payload = {"dither": 1 if dither else 0, "mac": display_mac.upper()}
    response = requests.post(url, data=payload, files={"file": buffer.getvalue()})
    response.raise_for_status()

upload_image("pem.jpg", DisplaySize.MEDIUM, "00000218A8663B10", "192.168.178.238", dither=True)