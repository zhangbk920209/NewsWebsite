from flask import render_template

from . import news_blue


@news_blue.route('/')
def index():
    return render_template('news/index.html')
