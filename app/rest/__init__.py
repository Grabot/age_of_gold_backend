from flask import Blueprint

app_api = Blueprint('api', __name__)

from app.rest import map_rest
from app.rest.v1_0 import map_remove_row
from app.rest.v1_0 import map_remove
from app.rest.v1_0 import login
from app.rest.v1_0 import register
from app.rest.v1_0 import refresh
from app.rest.v1_0 import token_login
from app.rest.v1_0 import tile_change
from app.rest.v1_0 import get_hexagon
from app.rest.v1_0 import get_tile_info

