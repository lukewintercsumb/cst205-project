"""
This is the main file for the flask project "Car editor" for Team 477 in CST205
This module defines the different pages/routes and references functions from our utils.py module
It serves as the central hub for everything happening in our application
"""

from flask import Flask, render_template
from flask_bootstrap import Bootstrap5

app = Flask(__name__)
bootstrap = Bootstrap5(app)

@app.route('/')
def homepage():
    return render_template('homepage.html')