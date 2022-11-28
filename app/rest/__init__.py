from flask import Blueprint

app_api = Blueprint('api', __name__)


from app.rest import hexagon_rest
from app.rest import map_rest
from app.rest import map_row_rest
from app.rest import map_remove_row
from app.rest import map_remove
from app.rest import add_tile_detail
from app.rest import login_v1_1
from app.rest import register_v1_1
from app.rest import refresh_v1_1

