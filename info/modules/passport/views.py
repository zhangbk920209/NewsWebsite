import random, re

from datetime import datetime
from flask import request, jsonify, current_app, make_response
from flask import session

from info import constants, db
from info import redis_store
from info.libs.yuntongxun.sms import CCP
from info.models import User
from info.utils.captcha.captcha import captcha
from info.utils.response_code import RET

from . import passport_blue


@passport_blue.route('/image_code')
def image_code():
    # 获取参数
    image_code = request.args.get('image_code')
    # 检查参数
    if not image_code:
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 调用captcha生成图片验证码
    name, text, image = captcha.generate_captcha()
    # 存储图片验证码
    try:
        redis_store.setex('Imagecode_' + image_code, constants.IMAGE_CODE_REDIS_EXPIRES, text)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='图片验证码获取失败')
    # 返回结果
    response = make_response(image)
    return response


@passport_blue.route('/sms_code', methods=['POST'])
def sms_code():
    # 获取参数
    mobile = request.json.get('mobile')
    image_code = request.json.get('image_code')
    image_code_id = request.json.get('image_code_id')
    print(image_code)
    # 检查参数
    if not all([image_code, mobile]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='手机号格式错误')
    try:
        text = redis_store.get('Imagecode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='验证码已过期')
    try:
        redis_store.delete('Imagecode_' + image_code_id)
    except Exception as e:
        current_app.logger.error(e)
    print(text, image_code)
    if image_code.lower() != text.lower():
        return jsonify(errno=RET.PARAMERR, errmsg='图片验证码错误')
    try:
        mobile_list = User.query.filter(User.mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据异常')
    if mobile in mobile_list:
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')
    # 调用第三方工具发送短信
    sms_data = "%06d" % random.randint(1, 999999)
    print(sms_data)
    ccp = CCP()
    ccp.send_template_sms(mobile, [sms_data, constants.SMS_CODE_REDIS_EXPIRES / 60], 1)
    # 存储验证码信息
    try:
        redis_store.setex('smscode_' + mobile, constants.SMS_CODE_REDIS_EXPIRES, sms_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据异常')
    return jsonify(errno=RET.OK, errmsg='短信验证码已发送')


@passport_blue.route('/register', methods=['POST'])
def register():
    # 获取参数
    mobile = request.json.get('mobile')
    sms_code = request.json.get('sms_code')
    password = request.json.get('password')
    # 检查参数
    if not all([mobile, sms_code, password]):
        return jsonify(errno=RET.PARAMERR, errmsg='参数缺失')
    # 检查手机是否已注册
    try:
        mobile_list = User.query.filter(User.mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据异常')
    if mobile in mobile_list:
        return jsonify(errno=RET.DATAEXIST, errmsg='手机号已注册')
    try:
        real_sms_code = redis_store.get('smscode_' + mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg='数据异常')
    if real_sms_code != sms_code:
        return jsonify(errno=RET.PARAMERR, errmsg='短信验证码错误')
    user = User()
    user.mobile = mobile
    user.password = password
    user.nick_name = mobile
    try:
        db.session.add(user)
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    session['user_id'] = user.id
    session['mobile'] = mobile
    session['nick_name'] = mobile
    return jsonify(errno=RET.OK, errmsg='用户注册成功')


@passport_blue.route('/login', methods=['POST'])
def login():
    # 获取参数
    mobile = request.json.get('mobile')
    password = request.json.get('password')
    # 检查参数
    if not all([mobile, password]):
        return jsonify(errno=RET.PARAMERR,errmsg='参数缺失')
    # 手机号格式
    if not re.match(r'1[3456789]\d{9}$', mobile):
        return jsonify(errno=RET.PARAMERR, errmsg='参数格式错误')
    try:
        user = User.query.filter(User.mobile == mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR,errmsg='数据异常')
    # 检查账号密码
    if user is None or not user.check_password(password):
        return jsonify(errno=RET.NODATA,errmsg='用户名或密码错误')
    # 记录用户登陆时间
    user.last_login = datetime.now()
    # 提交数据
    try:
        db.session.commit()
    except Exception as e:
        current_app.logger.error(e)
        db.session.rollback()
        return jsonify(errno=RET.DBERR, errmsg='数据存储异常')
    # 业务处理
    session['mobile'] = mobile
    session['user_id'] = user.id
    session['nick_name'] = user.nick_name
    return jsonify(errno=RET.OK,errmsg='OK')


# 无请求数据 接收GET方法
@passport_blue.route('/logout')
def logout():
    session.pop('is_admin', None)
    session.pop('nick_name', None)
    session.pop('user_id', None)
    session.pop('mobile', None)
    return jsonify(errno=RET.OK,errmsg='退出成功')