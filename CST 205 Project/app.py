from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import re
from utils import apply_filter, edit_paint
from PIL import Image

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

selected_colors = []

PATH_TO_EDITED = os.path.join(app.config['UPLOAD_FOLDER'], 'car_edited.png')

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in app.config['ALLOWED_EXTENSIONS']

def sanitize_filename(filename):
    filename = re.sub(r'[^a-zA-Z0-9_.-]', '_', filename)
    return filename

@app.route('/')
def index():
    car_images = [f for f in os.listdir(app.config['UPLOAD_FOLDER']) if os.path.isfile(os.path.join(app.config['UPLOAD_FOLDER'], f))]
    return render_template('index.html', car_images=car_images)

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
    car_image = request.args.get('car_image')

    # creating the edited image from the selected original image
    original_image_path = car_image.replace(url_for('static', filename='images/'), '')
    original_image = Image.open(os.path.join(app.config['UPLOAD_FOLDER'], original_image_path))
    original_image.save(PATH_TO_EDITED)

    return render_template('intermediate.html', car_image=car_image, selected_colors=selected_colors)


@app.route('/add_color', methods=['POST'])
def add_color():
    color = request.form.get('color')
    if color and color not in selected_colors:
        selected_colors.append(color)
    return jsonify(selected_colors)

@app.route('/remove_color', methods=['POST'])
def remove_color():
    color = request.form.get('color')
    if color and color in selected_colors:
        selected_colors.remove(color)
    return jsonify(selected_colors)

@app.route('/edit', methods=['GET', 'POST'])
def edit():
    car_image = request.args.get('car_image')
    if request.method == 'POST':
        color = request.form.get('color')
        filter_name = request.form.get('filter')
        intensity = float(request.form.get('intensity', 1))

        if color:
            chosen_color = tuple(int(color[i:i+2], 16) for i in (1, 3, 5))
            print(f"Applying color: {chosen_color}")
            edit_paint(chosen_color)
        
        if filter_name:
            print(f"Applying filter: {filter_name} with intensity {intensity}")
            apply_filter(filter_name, intensity)

        # saving the changes to the edited image
        # timestamp = int(time.time())
        return redirect(url_for('edit', car_image=car_image))
    return render_template('editor.html', car_image=car_image)


@app.route('/continue', methods=['GET'])
def continue_edit():
    car_image = request.args.get('car_image')
    return redirect(url_for('edit', car_image=car_image))





