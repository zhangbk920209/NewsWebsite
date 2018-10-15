from flask import current_app
from flask import render_template, app

from . import news_blue


@news_blue.route('/')
def index():
    return render_template('news/index.html')


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
