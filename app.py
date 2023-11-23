import uuid
from flask import Flask, jsonify, request, url_for
from enum import Enum, auto
import io
import requests
from flask import Flask, render_template
from enum import Enum, auto
import draw_image
from PIL import Image
from requests.exceptions import ConnectionError

app = Flask(__name__)

AP_IP = "192.168.178.239"

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


def upload_image(image_path:str, display_size: DisplaySize, display_mac:str, ap_url:str, dither=False):
    rgb_image = Image.open(image_path)
    rgb_image = rgb_image.convert("RGB")
    # rgb_image = rgb_image.resize(display_size.size)
    buffer = io.BytesIO()
    rgb_image.save(buffer, "JPEG", quality="maximum")
    # rgb_image.save("testing.jpg", "JPEG", quality="maximum")
    url = "http://" + ap_url + "/imgupload"
    
    display_mac = display_mac.zfill(16)
    payload = {"dither": 1 if dither else 0, "mac": display_mac.upper()}
    try:
        response = requests.post(url, data=payload, files={"file": buffer.getvalue()})
    except ConnectionError as error:
        return jsonify({"message": "Could not connect to the access point", "file_name": image_path})
    print(response.text)
    return jsonify({"message": response.text, "file_name": image_path})

@app.route("/")
def index():
    return render_template(
        "index.html",
        bootstrap_css=url_for("static", filename="bootstrap.min.css"),
        bootstrap_js=url_for("static", filename="bootstrap.min.js"),
        jquery_js=url_for("static", filename="jquery.min.js"),
        example_image=url_for("static", filename="example.jpg"),
    )

@app.route('/image_upload', methods=['POST'])
def image_upload():
    print("image_upload")
    # Get the uploaded file from the request
    file = request.files['file']

    # Save the file to a temporary location
    temp_file_path = f"static/user/{uuid.uuid4().hex}.jpg"
    file.save(temp_file_path)

    mac_address = request.form.get('macAddress')
    display_size = DisplaySize[request.form["size"].upper()]

    return upload_image(temp_file_path, display_size, mac_address, AP_IP)


@app.route('/upload', methods=['POST'])
def generate_image():
    # Get the data from the POST request
    data = request.get_json()

    # Extract the name, pronouns, and mac address from the data
    name = data['nickname']
    pronouns = data['pronouns']
    mac_address = data['macAddress']
    display_size = DisplaySize[data["size"].upper()]
    font_path = f"{data['font']}.ttf"
    print(name, pronouns, mac_address)
    file_name = f"static/user/{uuid.uuid4().hex}.jpg"
    draw_image.generate_image(name, pronouns, file_name, font_path)
    return upload_image(file_name, display_size, mac_address, AP_IP)


if __name__ == '__main__':
    app.run()
