# coding:utf-8
# Author:hxj

from . import api
from ihome.utils.captcha.captcha import captcha
from ihome.utils.response_code import RET
from ihome import redis_store, db
from ihome.models import User
import constants
from flask import current_app, jsonify, make_response, request
from ihome.libs.yuntongxun.sms import CCP
import random
from ihome.tasks.sms.tasks import send_sms


# GET 127.0.0.1/api/v1.0/image_codes/<image_codes_id>

@api.route('/image_codes/<string:image_codes_id>')
def get_imgae_code(image_codes_id):
    """
    获取图片验证码
    :param image_codes_id: 验证码id
    :return: 正常：验证码图片 异常：返回json
    """
    # 生成验证码图片
    name, text, image_data = captcha.generate_captcha()
    # 验证码真实值与编号保存redis中
    # redis_store.set('image_code_%s' % image_codes_id, text)
    # redis_store.expired('image_code_%s' % image_codes_id, constants.IMAGE_CODE_EXPIRED_TIME)
    try:
        redis_store.setex('image_code_%s' % image_codes_id, constants.IMAGE_CODE_EXPIRED_TIME, text)
    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='save image code id failed')
    # 返回图片
    resp = make_response(image_data)
    resp.headers['Content-Type'] = 'image/jpg'
    return resp


# GET 127.0.0.1/api/v1.0/sms_codes/<mobile>?image_code=xxx&image_code_id=xxx
# @api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>')
# def get_sms_code(mobile):
#     image_code = request.args.get('image_code')
#     image_code_id = request.args.get('image_code_id')
#
#     if not all([image_code, image_code_id]):
#         return jsonify(errno=RET.PARAMERR, msg=u"参数错误")
#
#     # 从redis中获取图片验证码
#     try:
#         real_image_code = redis_store.get('image_code_%s' % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, msg=u'redis数据库异常')
#     # 判断是否过期
#     if real_image_code is None:
#         return jsonify(errno=RET.NODATA, msg=u'数据过期')
#
#     # 删除图片验证码，防止用户使用同一个验证码验证多次
#     try:
#         redis_store.delete('image_code_%s' % image_code_id)
#     except Exception as e:
#         current_app.logger.error(e)
#
#     # 全部小写进行判断
#     if real_image_code.lower() != image_code.lower():
#         return jsonify(errno=RET.DATAERR, msg=u'填写错误')
#
#     # 判断对于这个手机的操作在60s内有没有之前的记录
#     # 有 认为操作频繁，不作处理
#     try:
#         send_flag = redis_store.get('send_sms_code_%s' % mobile)
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if send_flag is not None:
#             # 表示60s内之前有过发送短信记录
#             return jsonify(errno=RET.REQERR, msg=u'请求过于频繁，60s后重试')
#
#     # 判断用户是否存在
#     try:
#         user = User.query.filter_by(mobile=mobile).first()
#     except Exception as e:
#         current_app.logger.error(e)
#     else:
#         if user != None:
#             return jsonify(errno=RET.DATAEXIST, msg=u'手机号已存在')
#     # 生成短信验证码
#     sms_code = '%06d' % random.randint(0, 999999)
#     try:
#         redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_EXPIRED_TIME, sms_code)
#         # 保存发送这个手机号的记录，防止60s再次发送的操作
#         redis_store.setex('send_sms_code_%s' % mobile, constants.SEND_SMS_CODE_EXPIRED_TIME, 1)
#
#     except Exception as e:
#         # 记录日志
#         current_app.logger.error(e)
#         return jsonify(errno=RET.DBERR, msg='save sms code id failed')
#     # 发送短信
#     ccp = CCP()
#     try:
#         ret = ccp.send_Templates_SMS(mobile, [sms_code, int(constants.SMS_CODE_EXPIRED_TIME / 60)], 1)
#     except Exception as e:
#         current_app.logger.error(e)
#         return jsonify(errno=RET.THIRDERR, msg=u'发送异常')
#
#     # 返回值
#     if ret == 0:
#         return jsonify(errno=RET.OK, msg=u'发送成功')
#     else:
#         return jsonify(errno=RET.THIRDERR, msg=u'发送失败')



@api.route('/sms_codes/<re(r"1[34578]\d{9}"):mobile>')
def get_sms_code(mobile):
    image_code = request.args.get('image_code')
    image_code_id = request.args.get('image_code_id')

    if not all([image_code, image_code_id]):
        return jsonify(errno=RET.PARAMERR, msg=u"参数错误")

    # 从redis中获取图片验证码
    try:
        real_image_code = redis_store.get('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'redis数据库异常')
    # 判断是否过期
    if real_image_code is None:
        return jsonify(errno=RET.NODATA, msg=u'数据过期')

    # 删除图片验证码，防止用户使用同一个验证码验证多次
    try:
        redis_store.delete('image_code_%s' % image_code_id)
    except Exception as e:
        current_app.logger.error(e)

    # 全部小写进行判断
    if real_image_code.lower() != image_code.lower():
        return jsonify(errno=RET.DATAERR, msg=u'填写错误')

    # 判断对于这个手机的操作在60s内有没有之前的记录
    # 有 认为操作频繁，不作处理
    try:
        send_flag = redis_store.get('send_sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if send_flag is not None:
            # 表示60s内之前有过发送短信记录
            return jsonify(errno=RET.REQERR, msg=u'请求过于频繁，60s后重试')

    # 判断用户是否存在
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
    else:
        if user != None:
            return jsonify(errno=RET.DATAEXIST, msg=u'手机号已存在')
    # 生成短信验证码
    sms_code = '%06d' % random.randint(0, 999999)
    try:
        redis_store.setex('sms_code_%s' % mobile, constants.SMS_CODE_EXPIRED_TIME, sms_code)
        # 保存发送这个手机号的记录，防止60s再次发送的操作
        redis_store.setex('send_sms_code_%s' % mobile, constants.SEND_SMS_CODE_EXPIRED_TIME, 1)

    except Exception as e:
        # 记录日志
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='save sms code id failed')
    #celery 异步 发送短信

    result = send_sms.delay(mobile, [sms_code, int(constants.SMS_CODE_EXPIRED_TIME / 60)], 1)
    print(result.id)

    # get方法获取celery异步执行结果
    # get方法默认阻塞，会等到执行结果才返回
    # 可接受参数timeout，超时时间，超过时间还拿不到结果，直接返回
    ret = result.get()
    print ret

    return jsonify(errno=RET.OK, msg=u'发送成功')