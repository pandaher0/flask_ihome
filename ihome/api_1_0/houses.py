# coding:utf-8
# Author:hxj
from . import api
from ihome.models import Area, House, Facility
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


@api.route('/house/info', methods=['POST'])
@login_required
def save_house_info():
    """
    存储房屋信息
    {
        'title':'',
        'price':'',
        'area_id':'',
        'address':'',
        'room_count':'',
        'acreage':'',
        'unit':'',
        'capacity':'',
        'beds':'',
        'deposit':'',
        'min_days':'',
        'max_days':'',
        'facility':'['7','8']',
    }
    :return:
    """
    user_id = g.user_id
    house_data = request.get_json()
    title = house_data.get('title')
    price = house_data.get('price')
    area_id = house_data.get('area_id')
    address = house_data.get('address')
    room_count = house_data.get('room_count')
    unit = house_data.get('unit')
    acreage = house_data.get('acreage')
    capacity = house_data.get('capacity')
    beds = house_data.get('beds')
    deposit = house_data.get('deposit')
    min_days = house_data.get('min_days')
    max_days = house_data.get('max_days')

    if not all([title, price, area_id, address, room_count, unit,
                acreage, capacity, beds, deposit, min_days, max_days]):
        return jsonify(errno=RET.PARAMERR, msg=u'缺少参数')

    # 判断价格、押金格式是否正确
    try:
        price = int(float(price) * 100)
        deposit = int(float(deposit) * 100)
    except Exception as e:
        current_app.loggere.error(e)
        return jsonify(errno=RET.PARAMERR, msg=u'请输入正确的价格，数字类型，最多2位小数')

    # 判断地区id是否在数据库中存在
    try:
        area = Area.query.get(area_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'数据库错误')

    if area is None:
        return jsonify(errno=RET.DBERR, msg=u'城区不存在')

    # 保存房屋信息
    house = House(
        user_id=user_id,
        area_id=area_id,
        title=title,
        price=price,
        address=address,
        room_count=room_count,
        unit=unit,
        acreage=acreage,
        capacity=capacity,
        beds=beds,
        deposit=deposit,
        min_days=min_days,
        max_days=max_days,
    )
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'数据库错误')

    # 处理房屋设施信息
    facility_ids = house_data.get('facility')
    # 如果用户勾选了信息，在保存数据
    if facility_ids:
        try:
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, msg=u'数据库错误')

        if facilities:
            # 表示有合法数据
