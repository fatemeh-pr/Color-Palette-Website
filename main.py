import os
import uuid
import pandas as pd
from flask import Flask, render_template, send_from_directory, session
from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms.validators import DataRequired, NumberRange
from wtforms.fields import IntegerField, SubmitField
from flask_uploads import UploadSet, IMAGES, configure_uploads
from color_extractor import ColorExtractor

app = Flask(__name__)
photos = UploadSet(name='photos', extensions=IMAGES)
app.config["UPLOADED_PHOTOS_DEST"] = "static/temp"
app.config["SECRET_KEY"] = os.environ.get("SECRET_KEY")
if not app.config["SECRET_KEY"]:
    raise RuntimeError(
        "SECRET_KEY environment variable is not set. "
        "Generate one with: python -c \"import secrets; print(secrets.token_hex())\""
    )
app.config["MAX_CONTENT_LENGTH"] = 16 * 1024 * 1024
configure_uploads(app, photos)

DEMO_IMAGE = "static/demo/demo_image.jpg"
DEMO_COLORS = pd.read_csv("static/demo/demo_color_palette.csv")


class ImageForm(FlaskForm):
    color_number = IntegerField(label="Number of Colors", validators=[DataRequired(), NumberRange(min=5, max=20)])
    photo = FileField(label="Image", validators=[FileRequired(), FileAllowed(photos, 'Images only!')])
    submit = SubmitField("Submit")


@app.route("/", methods=["GET", "POST"])
def home():
    form = ImageForm()
    image_path = DEMO_IMAGE
    colors = DEMO_COLORS

    if form.validate_on_submit():
        session["upload_id"] = str(uuid.uuid4())
        image_file = form.photo.data
        image_path = f"static/temp/{photos.save(image_file, session["upload_id"])}"
        n_color = form.color_number.data

        color_extractor = ColorExtractor()
        color_extractor.process_image(image_path)
        colors = color_extractor.extract_colors(n_color)
        color_extractor.save_csv(f"static/temp/{session["upload_id"]}/color_palette.csv")

    return render_template("index.html", form=form, photo=image_path, colors=colors)


@app.route("/save_csv")
def save_csv():
    upload_id = session.get("upload_id")
    if upload_id:
        path = f"static/temp/{session["upload_id"]}/color_palette.csv"
    else:
        path = "static/demo/demo_color_palette.csv"
    return send_from_directory(
        "static",
        path.removeprefix("static/"),
        as_attachment=True
    )


if __name__ == "__main__":
    app.run(debug=True)
