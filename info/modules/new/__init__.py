from flask import Blueprint, app

news_blue = Blueprint(app,__name__)

from . import views