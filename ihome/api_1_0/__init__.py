# coding:utf-8
# Author:hxj

from flask import Blueprint

# 创建蓝图对象
api = Blueprint('api_1_0', __name__)

# 导入蓝图视图
# demo  首页
# verify_code 图片验证码、短信验证码
# passport 注册、登录
# profile 个人信息页面、上传头像、修改昵称、实名认证
# houses 房屋相关
from . import demo, verify_code, passport, profile, houses
