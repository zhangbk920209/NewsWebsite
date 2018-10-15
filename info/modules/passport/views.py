import random, re
from flask import request, jsonify, current_app, make_response

from info import constants
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
    if image_code.lower() != text.lower():
        return jsonify(errno=RET.PARAMERR,errmsg='图片验证码错误')
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
    return jsonify(errno=RET.OK, errmsg='短信验证码已发送')
