from flask import Blueprint

passport_blue = Blueprint('pass_port', __name__)

from . import views