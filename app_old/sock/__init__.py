from flask import Blueprint

app_sock = Blueprint("sock", __name__)

from app_old.sock import sock
