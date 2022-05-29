from flask import Blueprint
from flask import render_template

app_api = Blueprint('api', __name__)


@app_api.route("/")
def home():
    return render_template('index.html')

