from flask import Flask, render_template, request, redirect, url_for, jsonify
from werkzeug.utils import secure_filename

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
app.config['SECRET_KEY'] = 'your_secret_key'  # chatGPT told me to add that because my application didn't let me use the Form without it
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

csrf.init_app(app)

selected_colors = []

PATH_TO_EDITED = os.path.join(app.config['UPLOAD_FOLDER'], 'car_edited.png')

class ImageForm(FlaskForm):
    # we are using the much appreciated FileField, which lets us capture the selected image
    file = FileField('Upload Image', validators=[DataRequired()])
    submit = SubmitField('Upload Image')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def sanitize_filename(filename):
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename

@app.route('/', methods=('GET', 'POST'))
def index():
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
    car_images = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return render_template('index.html', car_images=car_images, form=form)

@app.route('/upload', methods=['POST'])
def upload_file():
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
    global selected_colors
    selected_colors.clear()

    car_image_url = url_for('static', filename='images/car.png')
    # return render_template('intermediate.html', car_image=car_image, selected_colors=selected_colors)
    return render_template('intermediate.html', car_image_url=car_image_url, selected_colors=selected_colors, image_segmentation=image_segmentation)


@app.route('/add_color', methods=['GET', 'POST'])
@csrf.exempt
def add_color():
    print(request.form)
    color = request.form.get('color')
    if color and color not in selected_colors:
        selected_colors.append(color)
    return jsonify(selected_colors)

@app.route('/remove_color', methods=['POST'])
@csrf.exempt
def remove_color():
    color = request.form.get('color')
    if color and color in selected_colors:
        selected_colors.remove(color)
    return jsonify(selected_colors)

@app.route('/image_segmentation_route', methods=['POST'])
def image_segmentation_route():
    global selected_colors
    color_tuples = [tuple(map(int, color[4:-1].split(','))) for color in selected_colors]
    image_segmentation(color_tuples)
    return redirect(url_for('intermediate'))

@app.route('/edit', methods=['GET', 'POST'])
def edit():
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
        
        return redirect(url_for('edit', car_image=car_image))
    return render_template('editor.html', car_image=car_image)

@app.route('/reset', methods=['POST'])
def reset():
    revert_edited_image()
    return redirect(url_for('edit'))
        
@app.route('/continue', methods=['GET'])
def continue_edit():
    car_image = request.args.get('car_image')
    return redirect(url_for('edit', car_image=car_image))
