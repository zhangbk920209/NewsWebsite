from flask import current_app, jsonify, render_template, session, g
from flask import request

from info import constants, db
from info.models import User, Category, News, Comment
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
    try:
        news = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询异常')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='未发现数据')
    news_rank = []
    for new in news:
        news_rank.append(new.to_dict())

    data = {
        'user': user.to_dict() if user else None,
        'category_list': category_list,
        'news_rank': news_rank,
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
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,
                                                                                          constants.HOME_PAGE_MAX_NEWS,
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


@news_blue.route('/<int:news_id>')
@user_require
def get_news_detail(news_id):
    """
    新闻详情
       用户数据展示
       点击排行展示
       新闻数据展示
    :param news_id:
    :return:
   """
    user = g.user
    # 显示新闻点击排行
    try:
        news = News.query.order_by(News.clicks.desc()).limit(constants.CLICK_RANK_MAX_NEWS)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询异常')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='未发现数据')
    news_rank = []
    for new in news:
        news_rank.append(new.to_dict())
    # 显示新闻详情
    try:
        news_detail = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='新闻查询失败')
    if not news_detail:
        return jsonify(errno=RET.NODATA, errmsg='未发现数据')
    news_detail.clicks += 1
    # 更新数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    # 收藏或取消收藏开关
    is_collected = False
    # 判断用户是否登陆及是否收藏后决定显示新闻收藏情况
    if user and news in user.collection_news:
        is_collected = True
    # 显示评论信息
    try:
        comments = Comment.query.filter(Comment.news_id==news_detail.id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据查询异常')
    comments_list = []
    for comment in comments:
        comments_list.append(comment.to_dict())


    data = {
        'user': user.to_dict() if user else None,
        'news_rank': news_rank,
        'news_detail': news_detail,
        'is_collected': is_collected,
        'comment_list':comments_list
    }
    return render_template('news/detail.html', data=data)


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
