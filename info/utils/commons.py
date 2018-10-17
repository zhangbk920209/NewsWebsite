from flask import current_app, session, g
from info.models import User
# 导入使被装饰的函数的属性不发生变化的模块
import functools


# 定义检查用户是否登陆的装饰器
def user_require(func):
    # 使被装饰的函数函数名不发生改变
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        user = None
        # 判断缓存中是否有用户信息
        if user_id:
            try:
                user = User.query.get(user_id)
            except Exception as e:
                current_app.logger.error(e)
        g.user = user
        return func(*args, **kwargs)

    # 保持函数名不变化的第二种方式
    # wrapper.__name = func.__name__
    return wrapper


# 新闻点击量排行样式过滤器
def rank_filter(index):
    if index == 1:
        return 'first'
    elif index == 2:
        return 'second'
    elif index == 3:
        return 'third'
    else:
        return ''
