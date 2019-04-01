# coding:utf-8
# Author:hxj
from . import api
from ihome.models import Area
from ihome import db, redis_store
from flask import session, jsonify, g, current_app, request
from ihome.utils.response_code import RET
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from sqlalchemy.exc import IntegrityError
import re
import constants
import json


@api.route('/areas')
def get_area_info():
    # 尝试从redis中获取数据
    try:
        resp_json = redis_store.get('area_info')
    except Exception as e:
        current_app.logger.error(e)
    else:
        if resp_json is not None:
            current_app.logger.info('hit redis area_info')
            return resp_json, 200, {'Content-Type': 'application/json'}

    try:
        area_li = Area.query.all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(RET.DBERR, msg=u'查询错误')

    area_dict_li = []
    for area in area_li:
        area_dict_li.append(area.to_dict())

    # 将数据生成json字符串  list > str(json字符串)
    resp_dict = dict(errno=RET.OK, msg='OK', data=area_dict_li)
    resp_json = json.dumps(resp_dict)

    try:
        redis_store.setex('area_info', constants.AREA_INFO_REDIS_CACHE_EXPIRES, resp_json)
    except Exception as e:
        current_app.logger.error(e)

    return resp_json, 200, {'Content-Type': 'application/json'}
