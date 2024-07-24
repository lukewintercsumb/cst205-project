from flask import Flask, render_template, request, redirect, url_for, jsonify
import os
import re

app = Flask(__name__)

app.config['UPLOAD_FOLDER'] = os.path.join('static', 'images')
app.config['ALLOWED_EXTENSIONS'] = {'png', 'jpg', 'jpeg', 'gif'}

selected_colors = []

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
        return redirect(url_for('intermediate', car_image=url_for('static', filename='images/' + filename)))
    return redirect(request.url)

@app.route('/intermediate')
def intermediate():
    global selected_colors
    selected_colors.clear()
    car_image = request.args.get('car_image')
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



