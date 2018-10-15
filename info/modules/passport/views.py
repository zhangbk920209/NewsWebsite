from flask import request, jsonify, current_app, make_response
from info import redis_store, constants
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
