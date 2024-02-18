"""Main application file for the web server."""
try:
    import tomllib
except ImportError:
    # use tomli as drop in replacement for tomllib
    # only for python<3.11
    import tomli as tomllib
import base64
from io import BytesIO
import io
import uuid
from pathlib import Path
from PIL import Image

import requests.exceptions
from flask import Flask, jsonify, render_template, request, send_file, url_for

from .draw_image import generate_image
from .upload_image import send_image
from redis import Redis

from flask_caching import Cache

app = Flask(__name__)

app.config.from_file("../config.toml", load=tomllib.load, text=False, silent=True)
app.config.from_prefixed_env()

if "AP_IP" not in app.config:
    raise ValueError("AP_IP must be set in the config.toml or environment variables.")


class ImageDB:
    """A simple image database that stores images in the file system."""

    def __init__(self):
        self.base_path = Path("/tmp/zonen_tags/images")
        self.base_path.mkdir(parents=True, exist_ok=True)

    def get(self, image_uuid: str):
        """Load the image with the given uuid from the database."""
        return Image.open(self.base_path / f"{image_uuid}.png")

    def set(self, image: Image, image_uuid: str):
        """Save the image with the given uuid to the database."""
        image.save(self.base_path / f"{image_uuid}.png")


image_db = ImageDB()


def add_slug_and_icon(inputs):
    for row in inputs:
        for field in row:
            field["slug"] = field["name"].lower().replace(" ", "_")
            field["icon"] = "static/icons/" + field["icon"]


@app.route("/")
def index():
    """Render the index page."""
    inputs = [
        [{"name": "Nickname", "icon": "@.png"}],
        [{"name": "Habitat", "icon": "flag.png", "icon_slug": "first_line_icon"}],
        [
            {"name": "Space", "icon": "house.png", "icon_slug": "second_line_icon1"},
            {
                "name": "Languages",
                "icon": "speech_bubble.png",
                "icon_slug": "second_line_icon2",
            },
        ],
        [
            {"name": "DECT", "icon": "phone.png", "icon_slug": "third_line_icon1"},
            {
                "name": "Pronouns",
                "icon": "exclamation_mark.png",
                "icon_slug": "third_line_icon2",
            },
        ],
        # [{"name": "MAC Address", "icon": "mac.png"}],
    ]

    add_slug_and_icon(inputs)

    return render_template(
        "index.html",
        inputs=inputs,
        bootstrap_css=url_for("static", filename="bootstrap.min.css"),
        css=url_for("static", filename="style.css"),
        bootstrap_js=url_for("static", filename="bootstrap.bundle.min.js"),
        jquery_js=url_for("static", filename="jquery.min.js"),
        script_js=url_for("static", filename="script.js"),
        example_image=url_for("static", filename="example.jpg"),
        htmx_js=url_for("static", filename="htmx.min.js"),
        icons=[
            url_for("static", filename=path.relative_to("tag_configurator/static"))
            for path in Path("tag_configurator/static/icons").glob("*.png")
        ],
    )


@app.route("/image/<image_uuid>")
def get_image(image_uuid):
    """Get the image with the given uuid."""
    try:
        return send_file(image_db.get(image_uuid), mimetype="image/png")
    except KeyError:
        raise ValueError(f"Image with uuid {image_uuid} not found.")


@app.route("/image_upload", methods=["POST"])
def image_upload():
    """Upload an image to the access point."""
    print("image_upload")
    # Get the uploaded file from the request
    file = request.files["file"]

    mac_address = request.form.get("mac_address")

    image = Image.open(file)
    relative_file_name = f"image/{uuid.uuid4()}"
    try:
        response = send_image(image, mac_address, app.config["AP_IP"])
    except requests.exceptions.ConnectionError:
        return jsonify(
            {
                "message": f"Could not connect to the access point at {app.config['AP_IP']}.",
                "file_name": relative_file_name,
            }
        )
    except ValueError as error:
        return jsonify({"message": str(error), "file_name": relative_file_name})
    print(response.text)
    return jsonify({"message": response.text, "file_name": relative_file_name})


@app.route("/generate", methods=["POST"])
def generate():
    """Generate an image from the given data and upload it to the access point."""
    # Get the data from the POST request
    data = request.get_json()

    # Extract the name, and mac address from the data
    mac_address = data["mac_address"]
    del data["mac_address"]

    print(data)

    image = generate_image(
        data,
        template_image_path="tag_configurator/static/image_templates/37c3.png",
        output_path=None,
    )

    image_uuid = str(uuid.uuid4())
    image_db.set(image, image_uuid)

    relative_file_name = f"image/{image_uuid}"

    try:
        response = send_image(image, mac_address, app.config["AP_IP"])
    except requests.exceptions.ConnectionError:
        return jsonify(
            {
                "message": f"Could not connect to the access point at {app.config['AP_IP']}.",
                "file_name": relative_file_name,
            }
        )
    except ValueError as error:
        return jsonify({"message": str(error), "file_name": relative_file_name})
    print(response.text)
    return jsonify({"message": response.text, "file_name": relative_file_name})


if __name__ == "__main__":
    app.run()
