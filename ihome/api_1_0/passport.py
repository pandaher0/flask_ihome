# coding:utf-8
# Author:hxj
from . import api
from ihome import redis_store, db
from ihome.models import User
from flask import request, jsonify, current_app, session
import constants
from sqlalchemy.exc import IntegrityError
from ihome.utils.response_code import RET
import re


@api.route('/users', methods=['POST'])
def register():
    """
    :参数  手机号、短信验证码、密码、确认密码
    :请求格式 json
    :return:
    """
    req_dict = request.get_json()
    mobile = req_dict.get('mobile')
    sms_code = req_dict.get('sms_code')
    pwd = req_dict.get('password')
    pwd2 = req_dict.get('password2')

    if not all([mobile, sms_code, pwd]):
        return jsonify(errno=RET.PARAMERR, msg=u'缺少参数')

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, msg=u'手机号格式错误')
    # 验证两次密码是否一致
    if pwd != pwd2:
        return jsonify(errno=RET.PARAMERR, msg=u'两次密码不一致')
    # 从redis获取短信验证码
    try:
        real_sms_code = redis_store.get('sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'读取验证码异常')

    # 判断是否过期
    if real_sms_code is None:
        return jsonify(errno=RET.NODATA, msg=u'短信验证码已过期')

    # 判断填写验证码是否正确
    if sms_code != real_sms_code:
        return jsonify(errno=RET.PARAMERR, msg=u'验证码填写错误')

    # 删除redis中的短信验证码，防止重复验证
    try:
        redis_store.delete('sms_code_%s' % mobile)
    except Exception as e:
        current_app.logger.error(e)

    # 判断手机号是否注册过
    # try:
    #     user = User.query.filter_by(mobile=mobile).first()
    # except Exception as e:
    #     current_app.logger.error(e)
    #     return jsonify(errno=RET.DBERR, msg=u'数据库异常')
    # else:
    #     if user != None:
    #         return jsonify(errno=RET.DATAEXIST, msg=u'手机号已存在')

    # 保存用户数据到数据库
    user = User(name=mobile, mobile=mobile)
    user.password = pwd
    try:
        db.session.add(user)
        db.session.commit()
    except IntegrityError as e:
        # 表示手机号重复
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DATAEXIST, msg=u'手机号已存在')
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'数据库异常')

    return jsonify(errno=RET.OK, msg=u'注册成功')


@api.route('/session', methods=['POST'])
def login():
    """
    :param mobile
    :param password
    json格式
    :return:
    """
    # 接受参数
    # 校验参数
    req_dict = request.get_json()
    mobile = req_dict.get('mobile')
    pwd = req_dict.get('password')
    if not all([mobile, pwd]):
        return jsonify(errno=RET.PARAMERR, msg=u'用户名密码为空')

    # 判断手机号格式
    if not re.match(r"1[34578]\d{9}", mobile):
        return jsonify(errno=RET.PARAMERR, msg=u'手机号格式错误')

    # 判断错误次数，超过次数限制，则返回
    # access_nums_请求ip：次数
    ip = request.remote_addr

    try:
        access_num = redis_store.get('access_nums_%s' % ip)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if access_num is not None and int(access_num) >= constants.ACCESS_NUM:
            return jsonify(errno=RET.REQERR, msg=u'错误次数过多，请稍后再试')

    # 判断用户
    try:
        user = User.query.filter_by(mobile=mobile).first()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'数据库错误')

    if user is None or not user.check_password_hash(pwd):
        print ('=====================' + ip)
        try:

            redis_store.incr('access_nums_%s' % ip)
            redis_store.expire('access_nums_%s' % ip, constants.ERR_ACCESS_EXPIRE_TIME)
        except Exception as e:

            current_app.logger.error(e)

        return jsonify(errno=RET.DATAERR, msg=u'用户名或密码错误')

    # 保存登录状态到session
    session['name'] = user.name
    session['mobile'] = user.mobile
    session['user_id'] = user.id
    return jsonify(errno=RET.OK, msg=u'登录成功')


@api.route('/session', methods=['GET'])
def check_login():
    name = session.get('name')
    if name:
        return jsonify(errno=RET.OK, msg='true', data={'name': name})
    else:
        return jsonify(errno=RET.SESSIONERR, msg='false')


@api.route('/session', methods=['DELETE'])
def logout():
    session.clear()
    return jsonify(errno=RET.OK, msg='true')
