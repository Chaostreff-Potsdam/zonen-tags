"""Main application file for the web server."""
try:
    import tomllib
except ImportError:
    # use tomli as drop in replacement for tomllib
    # only for python<3.11
    import tomli as tomllib
import base64
from io import BytesIO
import uuid
from pathlib import Path
from PIL import Image

import requests.exceptions
from flask import Flask, jsonify, render_template, request, send_file, url_for

from .draw_image import generate_image
from .upload_image import upload_image


from flask_caching import Cache

app = Flask(__name__)
# tell Flask to use the above defined config


app.config.from_file("../config.toml", load=tomllib.load, text=False, silent=True)
app.config.from_prefixed_env()

if "AP_IP" not in app.config:
    raise ValueError("AP_IP must be set in the config.toml or environment variables.")

cache = Cache(app)


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

    for row in inputs:
        for field in row:
            field["slug"] = field["name"].lower().replace(" ", "_")
            field["icon"] = "static/icons/" + field["icon"]

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
        image = cache.get(image_uuid)

        img_io = BytesIO()
        image.save(img_io, "JPEG", quality="maximum")
        img_io.seek(0)
        return send_file(img_io, mimetype="image/jpeg")
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
        response = upload_image(image, mac_address, app.config["AP_IP"])
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


@app.route("/upload", methods=["POST"])
def upload():
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
    cache.set(image_uuid, image)
    relative_file_name = f"image/{image_uuid}"

    try:
        response = upload_image(image, mac_address, app.config["AP_IP"])
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
