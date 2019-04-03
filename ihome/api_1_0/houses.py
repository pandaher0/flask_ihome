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
from datetime import datetime
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
    # 先进行session存储，暂不提交，无需try。 house、facility一并提交，要么都提交成功，要么都失败

    # 处理房屋设施信息
    facility_ids = house_data.get('facility')
    # 如果用户勾选了信息，在保存数据       ['1','2','3']
    if facility_ids:
        try:  # select * from Facility where id in []
            facilities = Facility.query.filter(Facility.id.in_(facility_ids)).all()
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, msg=u'数据库异常')

        if facilities:
            # 表示有合法数据
            house.facilities = facilities
    try:
        db.session.add(house)
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'保存数据失败')

    # 成功
    return jsonify(errno=RET.OK, msg='创建成功', data={'house_id': house.id})


@api.route('/house/image', methods=['POST'])
@login_required
def save_house_image():
    # 接受参数
    image = request.files.get('house_image')
    house_id = request.form.get('house_id')
    # 校验
    if not all([image, house_id]):
        return jsonify(errno=RET.NODATA, msg=u'缺少参数')

    try:
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'数据异常')

    if house is None:
        return jsonify(errno=RET.NODATA, msg=u'房屋不存在')

    # 存储图片到七牛
    image_data = image.read()

    try:
        filename = storage(image_data)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.THIRDERR, msg=u'保存图片失败')

    house_image = HouseImage(house_id=house_id, url=filename)
    db.session.add(house_image)
    # 处理房屋主图片
    if not house.index_image_url:
        house.index_image_url = filename
        db.session.add(house)

    try:
        db.session.commit()
    except Exception as e:
        db.session.rollback()
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'保存失败')

    img_url = constants.QINIU_URL_DOMAIN + house_image.url

    return jsonify(errno=RET.OK, msg=u'保存成功', data={'img_url': img_url})


@api.route('/user/houses', methods=['GET'])
@login_required
def get_my_house():
    user_id = g.user_id
    try:
        user = User.query.get(user_id)
        houses = user.houses
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'获取数据失败')

    houses_li = []
    if houses:
        for house in houses:
            houses_li.append(house.to_basic_dict())

    return jsonify(errno=RET.OK, errmsg='OK', data={'houses': houses_li})


@api.route('/houses/index', methods=['GET'])
def get_index_house():
    try:
        house_json = redis_store.get('home_page_pic')
    except Exception as e:
        current_app.logger.error(e)
    else:
        if house_json:
            current_app.logger.info('hit redis')
            return '{"errno":0, "msg":"成功", "data":%s}' % house_json, 200, {'Content-Type': 'application/json'}

    try:
        houses = House.query.order_by(House.order_count.desc()).limit(constants.HOME_PAGE_MAX_HOUSES)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg=u'数据库异常')

    if not houses:
        return jsonify(errno=RET.NODATA, msg=u'无数据')

    houses_li = []
    for house in houses:
        # 判断house是否设置了主页图片，空则跳过
        if not house.index_image_url:
            continue
        houses_li.append(house.to_basic_dict())

    # 返回json格式数据
    house_json = json.dumps(houses_li)
    print house_json

    try:
        redis_store.setex('home_page_pic', constants.HOME_PAGE_DATA_REDIS_EXPIRES, house_json)
    except Exception as e:
        current_app.logger.error(e)

    # 以字符串拼接方式记性返回，一定注意json格式，key加引号，冒号
    return '{"errno":"0", "msg":"成功", "data":%s}' % house_json, 200, {'Content-Type': 'application/json'}


@api.route('/house/<int:house_id>', methods=['GET'])
def get_house_detail(house_id):
    """获取房屋详情"""
    # 前端在房屋详情页面展示时，如果浏览页面的用户不是该房屋的房东，则展示预定按钮，否则不展示，
    # 所以需要后端返回登录用户的user_id
    # 尝试获取用户登录的信息，若登录，则返回给前端登录用户的user_id，否则返回user_id=-1
    user_id = session.get('user_id', '-1')
    if not house_id:
        return jsonify(errno=RET.PARAMERR, msg='缺少参数')

    try:
        house_json = redis_store.get('house_detail_info_%d' % house_id)
    except Exception as e:
        current_app.logger.error(e)
    else:
        if house_json:
            current_app.logger.info('hit redis detail')
            return '{"errno":0, "msg":"成功", "data":%s}' % house_json, 200, {'Content-Type': 'application/json'}

    try:
        user = User.query.get(user_id)
        house = House.query.get(house_id)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据库异常')

    if not house:
        return jsonify(errno=RET.NODATA, msg='无效房屋')

    data = {'house': house.to_full_dict(), 'user': user.to_dict()}
    data = json.dumps(data)
    redis_store.setex('house_detail_info_%d' % house_id, constants.HOUSE_DETAIL_REDIS_EXPIRE_SECOND, data)

    return '{"errno":0, "msg":"成功", "data":%s}' % data, 200, {'Content-Type': 'application/json'}


# GET /api/v1.0/houses?sd=2019-04-01&ed=2019-04-30&sk=new&aid=10&p=1
@api.route("/houses", methods=['GET'])
def get_house_list():
    start_date = request.args.get('sd', '')
    end_date = request.args.get('ed', '')
    area_id = request.args.get('aid', '')
    sort_key = request.args.get('sk', 'new')
    page = request.args.get('p')

    try:
        if start_date:
            start_date = datetime.strptime(start_date, '%Y-%m-%d')

        if end_date:
            end_date = datetime.strptime(end_date, '%Y-%m-%d')

        if start_date and end_date:
            assert start_date <= end_date
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.PARAMERR, msg='日期参数有误')

    # 判断区域id
    area = None
    if area_id:
        try:
            area = Area.query.get(area_id)
        except Exception as e:
            current_app.logger.error(e)
            return jsonify(errno=RET.DBERR, msg='区域参数有误')

    try:
        page = int(page)
    except Exception as e:
        current_app.logger.error(e)
        page = 1

    # 获取缓存
    # key = house_起始_结束_区域id_排序
    redis_key = 'house_%s_%s_%s_%s' % (start_date, end_date, area_id, sort_key)
    try:
        resp_json = redis_store.hget(redis_key, page)
    except Exception as e:
        current_app.logger.error(e)
        resp_json = None

    if resp_json:
        current_app.logger.info('hit redis list')
        return resp_json, 200, {'Content-Type': 'application/json'}

    # 构造参数列表容器
    filter_params = []

    # 时间条件
    # 查询所有时间冲突的房子
    # select * from order where order.begin_date<=end_date and order.end_date>=start_date
    try:
        if start_date and end_date:
            confict_orders = Order.query.filter(Order.begin_date <= end_date, Order.end_date >= start_date).all()
        elif start_date:
            confict_orders = Order.query.filter(Order.end_date >= start_date).all()
        elif end_date:
            confict_orders = Order.query.filter(Order.begin_date <= end_date).all()
        else:
            confict_orders = None
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据查询失败')

    if confict_orders:
        confict_house_ids = [order.house_id for order in confict_orders]
        # 冲突房屋id不为空
        if confict_house_ids:
            # 追加条件
            filter_params.append(House.id.notin_(confict_house_ids))

    # 区域条件
    if area:
        filter_params.append(House.area_id == area.id)

    # 排序
    if sort_key == 'booking':  # 入住最多
        house_query = House.query.filter(*filter_params).order_by(House.order_count.desc())
    elif sort_key == 'price-inc':  # 价格从低到高
        house_query = House.query.filter(*filter_params).order_by(House.price)
    elif sort_key == 'price-des':  # 价格从高到低
        house_query = House.query.filter(*filter_params).order_by(House.price.desc())
    else:  # new  默认 从新到旧
        house_query = House.query.filter(*filter_params).order_by(House.create_time.desc())

    # 分页
    try:
        #                                 当前页数        每页数量                                 自动错误输出
        paginater = house_query.paginate(page=page, per_page=constants.HOUSE_LIST_PAGE_CAPACITY, error_out=False)
    except Exception as e:
        current_app.logger.error(e)
        return jsonify(errno=RET.DBERR, msg='数据查询失败')

    # 获取页面数据
    house_li = paginater.items
    houses = []
    for house in house_li:
        houses.append(house.to_basic_dict())

    # 获取总页数
    total_page = paginater.pages

    resp_dict = dict(errno=RET.OK, msg='OK', data={'total_page': total_page, 'houses': houses, 'current_page': page})
    resp_json = json.dumps(resp_dict)

    # 设置缓存数据
    # value = { '1':{},'2':{} }
    if page <= total_page:
        try:
            # redis pipeline管道，类似mysql事务，但区别于不能回滚
            # redis_store.hset(redis_key, page, resp_json)
            # redis_store.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)
            # 创建管道
            pipeline = redis_store.pipeline()
            pipeline.multi()  # 事务开始
            pipeline.hset(redis_key, page, resp_json)
            pipeline.expire(redis_key, constants.HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES)
            pipeline.execute()  # 提交

        except Exception as e:
            current_app.logger.error(e)

    return resp_json, 200, {'Content-Type': 'application/json'}
