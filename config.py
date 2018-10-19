from redis import StrictRedis

# 定义redis链接信息常量
REDIS_HOST = '127.0.0.1'
REDIS_PORT = 6379


class Config:
    DEBUG = None
    # 设置秘钥
    SECRET_KEY = '91Ob0mObEHlxmG+r+BeQaF+u8KZpnpRNO9qXcIfRp17tBbCXDqflAdiOGDMbbMnag+U='

    # 配置状态保持相关信息
    SESSION_TYPE = 'redis'  # 缓存数据存储库类型设置为redis
    SESSION_REDIS = StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    SESSION_USE_SIGNER = True  # session签名,开启返回给浏览器cookie `session`值的加密
    PERMANENT_SESSION_LIFETIME = 86400  # 设置缓存信息有效期

    # 配置SQLAlchemy相关信息
    SQLALCHEMY_DATABASE_URI = 'mysql://root:mysql@localhost/info'
    SQLALCHEMY_TRACK_MODIFICATIONS = False


class Development(Config):
    DEBUG = True


class Production(Config):
    DEBUG = False


config_dict = {
    'development': Development,
    'Production': Production
}
