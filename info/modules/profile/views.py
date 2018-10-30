from flask import redirect, jsonify, g, render_template, request, current_app, session
from info.models import News, Category, User
from info import constants
from info.utils.image_storage import storage
from info import db
from . import profile_blue
from info.utils.commons import user_require
from info.utils.response_code import RET


@profile_blue.route('/user', methods=['GET', 'POST'])
@user_require
def user_info():
    user = g.user
    if not user:
        return redirect('/')
    data = {
        'user': user.to_dict()
    }
    return render_template('news/user.html', data=data)


@profile_blue.route('/base_info', methods=['GET', 'POST'])
@user_require
def base_info():
    """
    基本资料的展示和修改
    1、尝试获取用户信息
    2、如果是get请求，返回用户信息给模板
    如果是post请求：
    1、获取参数，nick_name,signature,gender[MAN,WOMAN]
    2、检查参数的完整性
    3、检查gender性别必须在范围内
    4、保存用户信息
    5、提交数据
    6、修改redis缓存中的nick_name
    注册：session['nick_name'] = mobile
    登录：session['nick_name'] = user.nick_name
    修改：session['nick_name'] = nick_name
    7、返回结果
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if request.method == 'GET':
        data = {
            'user': user.to_dict
        }
        return render_template('news/user_base_info.html', data=data)
    # 获取参数
    nick_name = request.json.get('nick_name')
    signature = request.json.get('signature')
    gender = request.json.get('gender')
    if not all([nick_name, signature, gender]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    if gender not in ['MAN', 'WOMAN']:
        return jsonify(errno=RET.PARAMERR, errmsg='参数范围异常')
    user.nick_name = nick_name
    user.signature = signature
    user.gender = gender
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    session['nick_name'] = nick_name
    print(jsonify(errno=RET.OK, errmsg='OK'))
    return jsonify(errno=RET.OK, errmsg='OK')


@profile_blue.route('/pic_info', methods=['GET', 'POST'])
@user_require
def pic_info():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if request.method == 'GET':
        data = {
            'user': user.to_dict()
        }
        return render_template('news/user_pic_info.html', data=data)
    try:
        avatar_data = request.files.get('avatar').read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='图片上传异常')
    try:
        avatar_url = storage(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='图片存储异常')

    user.avatar_url = avatar_url
    print(avatar_url)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    return jsonify(errno=RET.OK, errmsg='OK', data={"avatar_url": constants.QINIU_DOMIN_PREFIX + avatar_url})


@profile_blue.route('/user_follow', methods=['GET', 'POST'])
@user_require
def user_follow():
    user = g.user
    # 判断用户是否登录
    if not user:
        return jsonify(errno=RET.SESSIONERR,errmsg='用户未登录')
    # 获取当前页 默认为1
    current_page = request.args.get('current_page', 1)
    total_page = 1
    paginate = user.followed.paginate(current_page, total_page, False)
    items = paginate.items
    users = [user.to_dict() for user in items]
    if request.method == 'GET':
        data = {
            'current_page': current_page,
            'total_page': total_page,
            'users': users
        }
        return render_template('news/user_follow.html',data=data)
    current_page = paginate.page
    total_page = paginate.pages
    # data =
    return jsonify(errno=RET.OK,errmsg='OK')

    pass


@profile_blue.route('/password_change', methods=['GET', 'POST'])
@user_require
def password_change():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if request.method == 'GET':
        return render_template('news/user_pass_info.html')
    old_password = request.json.get('old_password')
    new_password = request.json.get('new_password')
    if not all([new_password, old_password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    try:
        user.password = new_password
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    return jsonify(errno=RET.OK, errmsg='OK')


@profile_blue.route('/user_collection')
@user_require
def user_collection():
    """
    用户收藏
    1、获取参数，页数p，默认1
    2、判断参数，整型
    3、获取用户信息，定义容器存储查询结果，总页数默认1，当前页默认1
    4、查询数据库，从用户收藏的的新闻中进行分页，user.collection_news
    5、获取总页数、当前页、新闻数据
    6、定义字典列表，遍历查询结果，添加到列表中
    7、返回模板news/user_collection.html,'total_page',current_page,'collections'
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    page = request.args.get('page', 1)
    paginate = user.collection_news.paginate(page, constants.USER_COLLECTION_MAX_NEWS, False)
    total_page = paginate.pages
    current_page = paginate.page
    news_list = paginate.items
    data = {
        'total_page': total_page,
        'news_list': news_list,
        'current_page': current_page
    }

    return render_template('news/user_collection.html', data=data)


@profile_blue.route('/user_news_release', methods=['GET', 'POST'])
@user_require
def user_news_release():
    """
    新闻发布：
    如果是get请求，加载新闻分类，需要移除'最新'分类，传给模板
    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if request.method == 'GET':
        categories = Category.query.filter(Category.id > 1).all()
        category_list = []
        for category in categories:
            category_list.append(category.to_dict())
        data = {
            'category': category_list
        }
        return render_template('news/user_news_release.html', data=data)
    pic_url = request.files.get('pic_url')
    digest = request.form.get('digest')
    content = request.form.get('content')
    title = request.form.get('title')
    category_id = request.form.get('category_id')
    if not all([pic_url, digest, content, title, category_id]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    try:
        category_id = int(category_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='数据类型转换异常')
    # 存储图片
    try:
        image_data = pic_url.read()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, errmsg='图片读取异常')
    # 使用七牛云存储图片
    try:
        image_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, errmsg='图片存储异常')
    new = News()
    new.category_id = category_id
    new.index_image_url = constants.QINIU_DOMIN_PREFIX + image_name
    new.content = content
    # new.create_time = datetime.datetime.now()
    new.user_id = user.id
    new.digest = digest
    new.title = title
    new.status = 1
    new.source = '个人发布'
    try:
        db.session.add(new)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    return jsonify(errno=RET.OK, errmsg='新闻发布成功')


@profile_blue.route('/user_news_list', methods=['GET', 'POST'])
@user_require
def user_news_list():
    """
    用户新闻列表
    1、获取参数，页数p，默认1
    2、判断参数，整型
    3、获取用户信息，定义容器存储查询结果，总页数默认1，当前页默认1
    4、查询数据库，查询新闻数据并进行分页，
    5、获取总页数、当前页、新闻数据
    6、定义字典列表，遍历查询结果，添加到列表中
    7、返回模板news/user_news_list.html 'total_page',current_page,'news_dict_list'

    :return:
    """
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if request.method == 'GET':
        paginate = user.news_list.order_by(News.create_time.desc()).paginate()
        news_list = paginate.items
        total_page = paginate.pages
        current_page = paginate.page
        data = {
            'news_list': news_list,
            'total_page': total_page,
            'current_page': current_page
        }
        return render_template('news/user_news_list.html', data=data)
    pass


@profile_blue.route('/other_info')
@user_require
def other_info():
    """
    查询其他用户信息
    1、获取用户登录信息
    2、获取参数，user_id
    3、校验参数，如果不存在404
    4、如果新闻有作者,并且登录用户关注过作者，is_followed = False
    5、返回模板news/other.html，is_followed,user,other_info
    :return:
    """
    user = g.user
    other_id = request.args.get('id')
    try:
        other_user = User.query.get(other_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据库查询异常')
    if not other_user:
        return render_template('news/404.html')
    user = other_user.to_dict()

    return render_template('news/other.html')