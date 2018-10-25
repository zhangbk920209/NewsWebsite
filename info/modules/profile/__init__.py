from flask import Blueprint

profile_blue = Blueprint('profile_blue', __name__)

from . import views