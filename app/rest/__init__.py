from flask import Blueprint

app_api = Blueprint('api', __name__)


from app.rest import hexagon_rest
from app.rest import map_rest
from app.rest import test_rest


# @app_api.route("/")
# def home():
#     return render_template('index.html')

