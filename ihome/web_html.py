# coding:utf-8
# Author:hxj

from flask import Blueprint, current_app,make_response
from flask_wtf import csrf

# 提供静态文件的蓝图
html = Blueprint('web_html', __name__)


@html.route('/<re(r".*"):filename>')
def get_html(filename):
    if not filename:
        filename = 'index.html'
    if filename != 'favicon.ico':
        filename = 'html/' + filename

    csrf_token = csrf.generate_csrf()
    resp = make_response(current_app.send_static_file(filename))
    resp.set_cookie('csrf_token',csrf_token)

    return resp

