import logging
from logging.handlers import RotatingFileHandler

from redis import StrictRedis
from flask_session import Session
from flask_wtf import CSRFProtect, csrf
from config import config_dict, REDIS_HOST, REDIS_PORT
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

redis_store = StrictRedis(host=REDIS_HOST, port=REDIS_PORT, decode_responses=True)


def create_app(config_type):
    # 实例化Flask应用对象
    app = Flask(__name__)
    # 调用配置类
    app.config.from_object(config_dict[config_type])
    # 建立Flask对象与SQLAlchemy对象连接
    db.init_app(app)
    # 实例化Session对象
    Session(app)
    # 实例化CSRFProtect对象
    CSRFProtect(app)
    # 定义钩子函数
    @app.after_request
    def after_request(response):
        csrf_token = csrf.generate_csrf()
        response.set_cookie('csrf_token', csrf_token)
        return response

    # 导入蓝图对象并注册
    from info.modules.new import news_blue
    app.register_blueprint(news_blue)
    from info.modules.passport import passport_blue
    app.register_blueprint(passport_blue)
    return app
