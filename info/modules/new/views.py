from flask import current_app, jsonify, render_template, session, g
from flask import request

from info import constants, db
from info.models import User, Category, News, Comment, CommentLike
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
    cid = request.json.get('cid')
    page = request.json.get('page')
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
        paginate = News.query.filter(*filters).order_by(News.create_time.desc()).paginate(page,constants.HOME_PAGE_MAX_NEWS, False)
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
    # 收藏或取消收藏开关
    is_collected = False
    print(news_detail)
    print(user.collection_news)
    # 判断用户是否登陆及是否收藏后决定显示新闻收藏情况
    if user and news_detail in user.collection_news:
        is_collected = True
    # 显示评论信息
    try:
        comments = Comment.query.filter(Comment.news_id == news_detail.id).order_by(Comment.create_time.desc()).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据查询异常')
    # 评论点赞
    comment_dict_list = []
    for comment_haha in comments:
        comment_dict = comment_haha.to_dict()
        if user and comment_haha in user.comments_like_table:
            comment_dict['is_like'] = True
        else:
            comment_dict['is_like'] = False

        comment_dict_list.append(comment_dict)

    # if user:
    #     try:
    #         comment_ids = [comment.id for comment in comments_list]
    #         comment_likes = CommentLike.query.filter(CommentLike.comment_id.in_(comment_ids),CommentLike.user_id == user.id).all()
    #         comment_like_ids = [comment_like.comment_id for comment_like in comment_likes]
    #     except Exception as e:
    #         current_app.logger.error(e)
    #
    # for comment in comments_list:
    #     comment_dict = comment.to_dict()
    #     # 如果未点赞
    #     comment_dict['is_like'] = False
    #     # 如果点赞
    #     if comment_dict['id'] in comment_like_ids:
    #         comment_dict['is_like'] = True
    #     comment_dict_list.append(comment_dict)

    # 用户关注
    is_followed = False
    if user and news_detail.user_id in user.followers:
        is_followed = True

    # 更新数据库
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    data = {
        'user': user.to_dict() if user else None,
        'news_rank': news_rank,
        'news_detail': news_detail,
        'is_collected': is_collected,
        'comment_list': comment_dict_list,
        'is_followed':is_followed,
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
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
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
    parent_id = request.json.get('parent_id')
    # 检查参数
    if not all([comment_content, news_id]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    try:
       news_id = int(news_id)
       if parent_id:
           parent_id = int(parent_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='类型转换异常')
    # 查询数据库，确认新闻的存在
    try:
        news = News.query.get(news_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='查询新闻数据失败')
    # 判断查询结果
    if not news:
        return jsonify(errno=RET.NODATA, errmsg='新闻不存在')

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
    return jsonify(errno=RET.OK,errmsg='OK', data=comment.to_dict())


@news_blue.route('/comment_like',methods=['POST'])
@user_require
def comment_like():
    """
    点赞或取消点赞
    1、获取用户登录信息
    2、获取参数，comment_id,action
    3、检查参数的完整性
    4、判断action是否为add，remove
    5、把comment_id转成整型
    6、根据comment_id查询数据库
    7、判断查询结果
    8、判断行为是点赞还是取消点赞
    9、如果为点赞，查询改评论，点赞次数加1，否则减1
    10、提交数据
    11、返回结果
    :return:
    """
    # 判断用户
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    # 获取参数
    comment_id = request.json.get('comment_id')
    action = request.json.get('action')
    # 检查参数
    if not all([comment_id, action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    if action not in ['add', 'remove']:
        return jsonify(errno=RET.PARAMERR,errmsg='数据范围异常')
    try:
        comment_id = int(comment_id),
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='参数类型转换异常')
    # 业务逻辑
    try:
        comment = Comment.query.get(comment_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据操作异常')
    if not comment:
        return jsonify(errno=RET.NODATA,errmsg='评论不存在')
    if action == 'add':
        user.comments_like_table.append(comment)
        comment.like_count += 1
    else:
        user.comments_like_table.remove(comment)
        comment.like_count -= 1

    # if action == 'add':
    #     comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id, CommentLike.comment_id == comment.id).first()
    #     # 判断查询结果 如果没有点赞过
    #     if not comment_like_model:
    #         comment_like_model = CommentLike()
    #         comment_like_model.user_id = user.id
    #         comment_like_model.comment_id = comment_id
    #         db.session.add(comment_like_model)
    #         comment.like_count += 1
    # else:
    #     comment_like_model = CommentLike.query.filter(CommentLike.user_id == user.id, CommentLike.comment_id == comment.id)
    #     if comment_like_model:
    #         db.session.delete(comment_like_model)
    #         comment.like_count -= 1

    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')

    return jsonify(errno=RET.OK,errmsg='OK')


@news_blue.route('/followed_user', methods=['POST'])
@user_require
def followed_user():
    """
    关注与取消关注
    1、获取用户信息,如果未登录直接返回
    2、获取参数，user_id和action
    3、检查参数的完整性
    4、校验参数，action是否为followed，unfollow
    5、根据用户id获取被关注的用户
    6、判断获取结果
    7、根据对应的action执行操作，关注或取消关注
    8、返回结果
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='请先登录')
    user_id = request.json.get('user_id')
    action = request.json.get('action')
    if not all([user_id, action]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    try:
        user_id = int(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR,errmsg='数据类型转换异常')
    if action not in ['followed', 'unfollow']:
        return jsonify(errno=RET.PARAMERR,errmsg='数据范围异常')
    try:
        author = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库操作异常')
    if not author:
        return jsonify(errno=RET.NODATA,errmsg='作者不存在')
    if action == ' followed':
        user.followers.append(author)
    else:
        user.followers.remove(author)
    return jsonify(errno=RET.OK,errmsg='OK')


@news_blue.route('/favicon.ico')
def favicon():
    return current_app.send_static_file('news/favicon.ico')
