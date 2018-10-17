from flask import current_app, jsonify, render_template, session, g
from flask import request

from info import constants
from info.models import User, Category, News
from info.utils.response_code import RET
from . import news_blue
from info.utils.commons import user_require


@news_blue.route('/')
@user_require
def index():
    user = g.user

    # 显示新闻分类
    categories = []
    try:
        categories = Category.query.all()
    except Exception as e:
        current_app.logger.error(e)
    category_list = []
    for category in categories:
        category_list.append(category.to_dict())

    # 显示新闻点击排行
    news = []
    try:
        news = News.query.order_by(News.clicks).limit(6)
    except Exception as e:
        current_app.logger.error(e)
    news_list = []
    for new in news:
        news_list.append(new)

    data = {
        'user': user.to_dict() if user else None,
        'category_list': category_list,
        'news_list': news_list,
    }
    # 返回数据
    return render_template('news/index.html', data=data)


@news_blue.route('/news_list', methods=['POST'])
def news_list():
    # 获取参数
    cid = request.json.get('cid', '1')
    page = request.json.get('page', '1')
    # 参数均含默认值 不需检查 进行数据类型转换
    try:
        cid = int(cid)
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='数据类型异常')
    filters = []
    if cid > 1:
        filters.append(News.category_id == cid)
    try:
        paginate = News.query.filter(*filters).order_by(News.clicks).paginate(page, constants.HOME_PAGE_MAX_NEWS,
                                                                                False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询异常')
    items = paginate.items
    page = paginate.page
    total_page = paginate.pages
    news = []
    for item in items:
        news.append(item.to_dict())
    data = {
        'news_list': news,
        'page': page,
        'total_page': total_page
    }
    return jsonify(errno=RET.OK, errmsg='OK', data1=data)


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
