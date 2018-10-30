from flask import Blueprint

ademin_blue = Blueprint('admin_blue', __name__)

from . import views