# coding:utf-8
# Author:hxj

from flask import Blueprint

# 创建蓝图对象
api = Blueprint('api_1_0',__name__)

# 导入蓝图视图
from . import demo
from . import verify_code
from . import passport