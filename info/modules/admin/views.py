from flask import g, render_template, request, session, redirect, url_for, jsonify, current_app
from info.utils.response_code import RET
from info.models import User
from . import admin_blue
from info.utils.commons import user_require


@admin_blue.route('/index')
def index():
    user = g.user
    return render_template('admin/index.html', user=user.to_dict())


@admin_blue.route('/login', methods=['POST', 'GET'])
def admin_login():
    """
    后台管理员登录
    1、如果为get请求，使用session获取登录信息，user_id,is_admin,
    2、判断用户如果用户id存在并是管理员，重定向到后台管理页面
    3、获取参数，user_name,password
    4、校验参数完整性
    5、查询数据库，确认用户存在，is_admin为true，校验密码
    6、缓存用户信息，user_id,mobile,nick_name,is_admin
    7、跳转到后台管理页面

    :return:
    """
    if request.method == 'GET':
        user_id = session.get('user_id', None)
        is_admin = session.get('is_admin', False)
        if user_id and is_admin:
            return redirect(url_for('admin.index'))
        return render_template('admin/login.html')
    nick_name = request.form.get('nick_name')
    password = request.form.get('password')
    if not all([nick_name, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    try:
        user = User.query.filter(User.nick_name == nick_name, User.is_admin == True)
    except Exception as e:
        current_app.logger.error(e)
        return render_template('admin/login.html', errmsg='数据查询异常')
    if user is None or not user.check_password(password):
        return render_template('admin/login.html', errmsg='用户名或密码错误')
    session['is_admin'] = user.is_admin
    session['nick_name'] = user.nick_name
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    return redirect(url_for('admin.index'))
