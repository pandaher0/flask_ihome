# coding:utf-8
# Author:hxj
from . import api
from ihome.models import User
from ihome import db
from flask import session, jsonify, g, current_app, request
from ihome.utils.response_code import RET
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from sqlalchemy.exc import IntegrityError
import re
import constants


@api.route('/user', methods=['GET'])
@login_required
def user_file():
    user_id = g.user_id
    try:
        # user = User.query.filter_by(id=user_id).first()
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'获取数据失败')

    if user is None:
        return jsonify(errno=RET.NODATA, msg=u'无效操作')

    return jsonify(errno=RET.OK, msg='true',
                   data=user.to_dict())


@api.route('/user/avatar', methods=['POST'])
@login_required
def set_user_avatar():
    """
        参数：图片（多媒体表单） 用户id
        :return:
        """
    user_id = g.user_id

    pic = request.files.get('avatar')

    if pic is None:
        return jsonify(errno=RET.PARAMERR, msg=u'未上传图片')

    image_data = pic.read()
    try:
        file_name = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, msg=u'上传失败')

    # 保存文件名到数据库中
    try:
        User.query.filter_by(id=user_id).update({'avatar_url': file_name})
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'保存图片信息失败')

    # 保存成功放回

    return jsonify(errno=RET.OK, msg=u'保存成功', data={'avatar_url': constants.QINIU_URL_DOMAIN + file_name})


@api.route('/user/name', methods=['PUT'])
@login_required
def set_user_name():
    """
    参数：用户名 用户id
    :return:
    """
    user_id = g.user_id
    req_dict = request.get_json()
    name = req_dict.get('name')

    if name is None:
        return jsonify(errno=RET.PARAMERR, msg=u'用户名为空')

    if not re.match(r'^[a-zA-Z0-9_-]{4,16}$', name):
        return jsonify(errno=RET.PARAMERR, msg=u'4到16位（字母，数字，下划线，减号）')

    try:
        User.query.filter_by(id=user_id).update({'name': name})
        db.session.commit()
    except IntegrityError as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'用户名已被注册')
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'修改失败')

    session['name'] = name
    return jsonify(errno=RET.OK, msg=u'修改成功', data={'name': name})


@api.route('/user/auth', methods=['GET'])
@login_required
def get_user_auth():
    """获取用户的实名认证信息"""
    user_id = g.user_id

    # 在数据库中查询信息
    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, errmsg="获取用户实名信息失败")

    if user is None:
        return jsonify(errno=RET.NODATA, errmsg="无效操作")

    return jsonify(errno=RET.OK, errmsg="OK", data=user.auth_to_dict())


@api.route('/user/auth', methods=['POST'])
@login_required
def set_user_auth():
    user_id = g.user_id
    req_dict = request.get_json()
    real_name = req_dict.get('real_name')
    id_card = req_dict.get('id_card')

    if not all([real_name, id_card]):
        return jsonify(errno=RET.PARAMERR, msg=u'内容为空')

    # 校验身份证
    if not re.match(r'^[1-9]\d{5}(18|19|([23]\d))\d{2}((0[1-9])|(10|11|12))(([0-2][1-9])|10|20|30|31)\d{3}[0-9Xx]$',
                    id_card):
        return jsonify(errno=RET.PARAMERR, msg=u'身份证号码格式错误')

    print req_dict
    try:
        User.query.filter_by(id=user_id,real_name=None,id_card=None).update({"real_name": real_name, "id_card": id_card})
        # user.id_card = id_card
        # user.real_name = real_name
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'存储失败')

    return jsonify(errno=RET.OK, msg='ok')
