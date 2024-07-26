"""
course: CST205
title: Paint editor
abstract: This application allows users to upload (one of the preselected options) an image of a car.
          The can use clever algorithms to select part of the paint, and then application will automatically make a selection of the paint.
          The user can then change the color of the paint and also apply filters and even choose the intensity of the filter
authors: Elina Adibi, William Hurley, Luke Winter, Samuel Scott
date: 07-26-24
note: All the CSRF had to be added to make sure that the form work. We are not sure why that is required, but potentially it is a mac issue.
"""

from flask import Flask, render_template, request, redirect, url_for, jsonify

# for the flask form
from flask_wtf import FlaskForm
from flask_wtf.csrf import CSRFProtect
from wtforms import SubmitField, FileField
from wtforms.validators import DataRequired

import shutil
import os
import re
from utils import apply_filter, edit_paint, image_segmentation, revert_edited_image
from PIL import Image

app = Flask(__name__)
csrf = CSRFProtect(app)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['SECRET_KEY'] = 'your_secret_key'
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

csrf.init_app(app)

selected_colors = []

PATH_TO_EDITED = os.path.join(app.config['UPLOAD_FOLDER'], 'car_edited.png')

class ImageForm(FlaskForm):
    """
    @author: Luke Winter
    ImageForm is an object that will allow us to upload images that we can reference later.
    """
    # we are using the much appreciated FileField, which lets us capture the selected image
    file = FileField('Upload Image', validators=[DataRequired()])
    submit = SubmitField('Upload Image')

def allowed_file(filename):
    """
    Simple method to check extension of filename
    @author: William Hurley
    """
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def sanitize_filename(filename):
    """
    Simple method to simplify the filename using regex
    @author: William Hurley
    """
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename

@app.route('/', methods=('GET', 'POST'))
def index():
    """
    @author: William Hurley and Luke Winter
    this is the route for the homepage. It instantiates a form object, which will give us access to the selected file. When the user submits the file,
    we create three copies of the selected image. These three copies are car.png, car_selection.png, car_edit.png and will be used in various ways in the following routes.
    """
    form = ImageForm()
    if form.validate_on_submit():
        print("HERE")
        file_name = form.file.data.filename
        print(file_name)
        original_path = os.path.join(app.config['UPLOAD_FOLDER'], file_name)
        original_filename = f'static/images/car.png'
        selection_filename = f'static/images/car_selection.png'
        edit_filename = f'static/images/car_edit.png'
        shutil.copy2(original_path, original_filename)
        shutil.copy2(original_path, selection_filename)
        shutil.copy2(original_path, edit_filename)
        return redirect('/intermediate')
    # load the file name for the different preselectable options. This is a bit restrictive, but it'll do for now.
    car_images = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return render_template('index.html', car_images=car_images, form=form)

@app.route('/upload', methods=['POST'])
def upload_file():
    """
    @author: William Hurley
    This route enable file uploading. It clears previous colors from the list. It checks the file name to make sure it works properly.
    """
    global selected_colors
    selected_colors.clear()
    if 'file' not in request.files:
        return redirect(request.url)
    file = request.files['file']
    if file.filename == '':
        return redirect(request.url)
    if file and allowed_file(file.filename):
        filename = sanitize_filename(file.filename)
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)

        original_image = Image.open(file_path)
        original_image.save(PATH_TO_EDITED)

        return redirect(url_for('intermediate', car_image=url_for('static', filename='images/' + filename)))
    return redirect(request.url)

@app.route('/intermediate')
def intermediate():
    """
    @author: William Hurley
    simple route to show the page showing the two images and allowing users to select pixels.
    """
    global selected_colors
    selected_colors.clear()

    car_image_url = url_for('static', filename='images/car.png')
    # return render_template('intermediate.html', car_image=car_image, selected_colors=selected_colors)
    return render_template('intermediate.html', car_image_url=car_image_url, selected_colors=selected_colors, image_segmentation=image_segmentation)


@app.route('/add_color', methods=['GET', 'POST'])
@csrf.exempt
def add_color():
    """
    @author: William Hurley
    This method adds colors to the list of colors. It appends to the global variable defined earlier.
    It gets the color from the form that contains the colors and returns all selected colors as a json
    """
    print(request.form)
    color = request.form.get('color')
    if color and color not in selected_colors:
        selected_colors.append(color)
    return jsonify(selected_colors)

@app.route('/remove_color', methods=['POST'])
@csrf.exempt
def remove_color():
    """
    @author: William Hurley
    Simple method to remove a color from the form containing the color. The form is used both for adding and removing a color and acts as a data carrier from frontend to backend.
    """
    color = request.form.get('color')
    if color and color in selected_colors:
        selected_colors.remove(color)
    return jsonify(selected_colors)

@app.route('/image_segmentation_route', methods=['POST'])
def image_segmentation_route():
    """
    @author: Luke Winter
    This method is used to call the image_segmentation method.
    """
    global selected_colors
    print(selected_colors[0])
    # the colors are stored in a strange format: ImmutableMultiDict([('color', 'rgb(17,89,158)')])
    # so we apply some transformations to read each color individually and bring it in the format of a list of tuples
    color_tuples = [tuple(map(int, color[4:-1].split(','))) for color in selected_colors]
    image_segmentation(color_tuples)
    return redirect(url_for('intermediate'))

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    """
    @author: Elina Adibi
    This route handles the image editing fucntion. It allows the user to apply color changes, a filter and the filters intensity.
    It first loads the car image as a url, passes it to the template and displays it there. It obviously uses the car_edited.png image in the static/images directory.
    It uses a form to allow for color, filter and intensity selection. It calls apply_filter and edit_paint if the information was provided and is accessible in the form.
    """
    car_image = request.args.get('car_image', url_for('static', filename='images/car_edited.png'))
    print(f"Edit route called with car_image: {car_image}")
    if request.method == 'POST':
        color = request.form.get('color')
        filter_name = request.form.get('filter')
        intensity = request.form.get('intensity', 1)
        print(f"Received POST request with color: {color}, filter: {filter_name}, intensity: {intensity}")

        if color:
            chosen_color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            print(f"Applying color: {chosen_color}")
            edit_paint(chosen_color)

        if filter_name:
            print(f"Applying filter: {filter_name} with intensity {intensity}")
            apply_filter(filter_name, float(intensity))
        
        return redirect(url_for('edit', car_image=car_image)) # reload the page to show the updated image
    return render_template('editor.html', car_image=car_image)

@app.route('/reset', methods=['POST'])
def reset():
    """
    @author: Elina
    simple route to revert to original image
    """
    revert_edited_image()
    return redirect(url_for('edit'))
        
@app.route('/continue', methods=['GET'])
def continue_edit():
    """
    @author: Elina
    simple route to route to the edit page (reloads the page when already on the edit page)
    """
    car_image = request.args.get('car_image')
    return redirect(url_for('edit', car_image=car_image))
