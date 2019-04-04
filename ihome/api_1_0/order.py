# coding:utf-8
# Author:hxj
from . import api
from ihome.models import Area, House, Facility, HouseImage, User, Order
from ihome import db, redis_store
from flask import session, jsonify, g, current_app, request
from ihome.utils.response_code import RET
from ihome.utils.commons import login_required
from ihome.utils.image_storage import storage
from sqlalchemy.exc import IntegrityError
import re
from datetime import datetime, timedelta
import constants
import json


@api.route('/orders', methods=['POST'])
@login_required
def set_order():
    """
    user_id
    house_id
    begin_date
    end_date
    days = end_date-begin_date
    house_price = house.price
    amount = house_price * days + deposit
    status = WAIT_ACCEPT
    :return:
    """
    user_id = g.user_id
    req_dict = request.get_json()
    house_id = req_dict.get('house_id')
    start_date = req_dict.get('start_date')
    end_date = req_dict.get('end_date')

    if not req_dict:
        return jsonify(errno=RET.PARAMERR, msg='缺少参数')

    try:
        user = User.query.get(user_id)
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')

    if not all([user, house]):
        return jsonify(errno=RET.NODATA, msg='无效用户或房屋')

    if user_id == house.user_id:
        return jsonify(errno=RET.ROLEERR, msg='不能预定自己的房屋')

    try:
        begin_date = datetime.strptime(start_date, '%Y-%m-%d')
        end_date = datetime.strptime(end_date, '%Y-%m-%d')
        assert begin_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, msg='日期格式有误')

    try:
        confict_count = Order.query.filter(Order.house_id == house_id, Order.begin_date <= end_date,
                                           Order.end_date >= start_date).count()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据查询失败')

    if confict_count > 0:
        return jsonify(errno=RET.DATAERR, msg='房屋已被预定')

    days = (end_date - begin_date + timedelta(1)).days
    amount = house.price * days

    try:
        order = Order(user_id=user_id, house_id=house_id, begin_date=begin_date, end_date=end_date,
                      house_price=house.price, days=days, amount=amount)
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='存储失败')

    return jsonify(errno=RET.OK, msg='ok')


# /api/v1.0/orders?role=custom    landlord
@api.route('/orders', methods=['GET'])
@login_required
def get_order():
    user_id = g.user_id

    role = request.args.get('role', 'custom')

    try:
        user = User.query.get(user_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')

    if not user:
        return jsonify(errno=RET.NODATA, msg='无效用户')

    try:
        if role == 'landlord':

            houses = House.query.filter_by(user_id=user_id).all()
            house_ids = [house.id for house in houses]
            orders = Order.query.filter(Order.house_id.in_(house_ids))
        else:
            orders = Order.query.filter_by(user_id=user_id).all()
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')

    orders_li = []

    if orders:
        for order in orders:
            if order:
                orders_li.append(order.to_dict())
    else:
        return jsonify(errno=RET.NODATA, msg='无订单')

    return jsonify(errno=RET.OK, msg='ok', data=orders_li)


@api.route('/orders/<int:order_id>/status', methods=['PUT'])
@login_required
def change_status(order_id):
    req_dict = request.get_json()

    user_id = g.user_id
    action = req_dict.get('action')
    reason = req_dict.get('reason', '')

    if not all([action, order_id]) or action not in ['accept', 'reject']:
        return jsonify(errno=RET.NODATA, msg='参数错误')

    try:
        order = Order.query.filter(Order.id == order_id, Order.status == 'WAIT_ACCEPT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')

    if user_id != house.user_id:
        return jsonify(errno=RET.DBERR, msg='操作无效')

    if action == 'accept':
        order.status = 'WAIT_PAYMENT'
    else:
        order.status = 'REJECTED'
        order.comment = reason
    try:
        db.session.add(order)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')
    else:
        return jsonify(errno=RET.OK, msg='OK')


@api.route('/orders/<int:order_id>/comment', methods=['PUT'])
@login_required
def save_order_comment(order_id):
    req_dict = request.get_json()

    user_id = g.user_id
    comment = req_dict.get('comment', '')

    if not comment:
        return jsonify(errno=RET.NODATA, msg='参数错误')

    try:
        order = Order.query.filter(Order.id == order_id, Order.user_id == user_id,
                                   Order.status == 'WAIT_COMMENT').first()
        house = order.house
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')

    if not order:
        return jsonify(errno=RET.REQERR, msg='操作无效')

    try:
        order.status = 'COMPLETE'
        order.comment = comment

        house.order_count += 1

        db.session.add(order)
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')

    try:
        redis_store.delete('house_detail_info_%d' % house.id)
    except Exception as e:
        current_app.logger.error(e)


    return jsonify(errno=RET.OK, msg='OK')

@api.route('/orders/<int:order_id>/payment',methods=['POST'])
@login_required
def order_payment(order_id):
    pass
