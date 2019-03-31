# coding:utf-8
# Author:hxj


from werkzeug.routing import BaseConverter

from flask import session, jsonify,g
from response_code import RET
import functools

class REConverter(BaseConverter):
    def __init__(self, url_map, reqex):
        super(REConverter, self).__init__(url_map)
        self.regex = reqex


# 验证登录装饰器
def login_required(view_func):
    @functools.wraps(view_func)
    def wrapper(*args, **kwargs):
        user_id = session.get('user_id')
        if user_id is not None:
            # 将user_id保存到g对象中，此次请求时就可以通过g对象获取数据
            g.user_id =user_id
            return view_func(*args, **kwargs)
        else:
            return jsonify(errno=RET.SESSIONERR, msg=u'用户未登录')
        # 判断用户登录状态
        # 未登录，返回未登录信息

    return wrapper
