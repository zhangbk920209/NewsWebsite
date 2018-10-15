import logging
from logging.handlers import RotatingFileHandler

from config import config_dict
from flask import Flask
from flask_sqlalchemy import SQLAlchemy

logging.basicConfig(level=logging.DEBUG)  # 设置日志等级、调试debug级
# 创建日志记录器，指明日志保存的路径、每个日志文件的最大大小、保存的日志文件个数上限
file_log_handler = RotatingFileHandler("logs/log", maxBytes=1024 * 1024 * 100, backupCount=10)
# 创建日志记录的格式 日志等级 输入日志信息的文件名 行数 日志信息
formatter = logging.Formatter('%(levelname)s %(filename)s:%(lineno)d %(message)s')
# 为刚创建的日志记录器设置日志记录格式
file_log_handler.setFormatter(formatter)
# 为全局的日志工具对象（flask app使用的）添加日志记录器
logging.getLogger().addHandler(file_log_handler)

# 实例化SQLAlchemy类对象
db = SQLAlchemy()


def create_app(config_type):
    # 实例化Flask应用对象
    app = Flask(__name__)
    # 调用配置类
    app.config.from_object(config_dict[config_type])
    # 建立Flask对象与SQLAlchemy对象连接
    db.init_app(app)
    return app
