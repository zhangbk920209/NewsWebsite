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
        comments = Comment.query.filter(Comment.news_id == news_detail.id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询异常')
    comments_list = []
    son_comments_list = []
    for comment in comments:
        if not comment.parent:
            comments_list.append(comment.to_dict())
        else:
            son_comments_list.append(comment.to_dict())
    data = {
        'user': user.to_dict() if user else None,
        'news_rank': news_rank,
        'news_detail': news_detail,
        'is_collected': is_collected,
        'comment_list': comments_list,
        'son_comments_list': son_comments_list
    }
    return render_template('news/detail.html', data=data)


@news_blue.route('/news_collection', methods=['POST'])
@user_require
def news_collection():
    """
    新闻收藏和取消收藏
    1、获取参数，news_id,action[collect,cancel_collect]
    2、检查参数的完整性
    3、转换news_id参数的数据类型
    4、检查action参数的范围
    5、查询mysql确认新闻的存在
    6、校验查询结果
    7、判断用户选择的是收藏，还要判断用户之前未收藏过
    user.collection_news.append(news)
    如果是取消收藏
    user.collection_news.remove(news)
    8、提交数据mysql
    9、返回结果
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    news_id = request.json.get('news_id')
    action = request.json.get('action')
    if not all([news_id, action]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    try:
        news_id = int(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='数据类型转换异常')
    if action not in ['collect', 'cancel_collect']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数范围异常')
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据库查询异常')
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')
    if action == 'collect' and news not in user.collection_news:
        user.collection_news.append(news)
    else:
        user.collection_news.remove(news)
    return jsonify(errno=RET.OK, errmsg='OK')


@news_blue.route('/comment', methods=['POST'])
@user_require
def add_comment():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    # 获取参数
    comment_content = request.json.get('comment')
    news_id = request.json.get('news_id')
    parent_id = request.json.get('parent_id', '0')
    # 检查参数
    if not all([comment_content, news_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    try:
        parent_id, news_id,parent_id = int(parent_id), int(news_id), int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='类型转换异常')

    comment = Comment()
    comment.content = comment_content
    if parent_id != 0:
        comment.parent_id = parent_id
    comment.news_id = news_id
    comment.user_id = user.id
    try:
        db.session.add(comment)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    return jsonify(errno=RET.OK,errmsg='OK')


@news_blue.route('/comment_like')
@user_require
def haha():
    pass


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
