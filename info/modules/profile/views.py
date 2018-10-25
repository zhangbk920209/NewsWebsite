from flask import redirect, jsonify, g, render_template, request, current_app, session

from info import constants
from info.utils.image_storage import storage
from info import db
from . import profile_blue
from  info.utils.commons import user_require
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
        return jsonify(errno=RET.PARAMERR,errmsg='图片上传异常')
    try:
        avatar_url = storage(avatar_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR,errmsg='图片存储异常')

    user.avatar_url = avatar_url
    print(avatar_url)
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    return jsonify(errno=RET.OK,errmsg='OK', data={"avatar_url": constants.QINIU_DOMIN_PREFIX + avatar_url})


@profile_blue.route('/user_follow', methods=['GET', 'POST'])
@user_require
def user_follow():
    pass


@profile_blue.route('/password_change', methods=['GET', 'POST'])
@user_require
def password_change():
    user = g.user
    if not user:
        return jsonify(errno=RET.SESSIONERR, errmsg='用户未登录')
    if request.method == 'GET':
        print(request.method)
        render_template('news/user_pass_info.html')
    # old_password = request.json.get('old_password')
    # new_password = request.json.get('new_password')
    # if not all([new_password, old_password]):
    #     return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # try:
    #     user.password = new_password
    #     db.session.commit()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     db.session.rollback()
    #     return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    # return jsonify(errno=RET.OK,errmsg='OK')


@profile_blue.route('/user_collection', methods=['GET', 'POST'])
@user_require
def user_collection():
    pass


@profile_blue.route('/user_news_release', methods=['GET', 'POST'])
@user_require
def user_news_release():
    pass


@profile_blue.route('/user_news_list', methods=['GET', 'POST'])
@user_require
def user_news_list():
    pass
