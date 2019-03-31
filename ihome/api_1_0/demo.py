# coding:utf-8
# Author:hxj
from . import api
from flask import current_app
from ihome import db,models

@api.route('/index')
def index():
    current_app.logger.error('ERROR')
    current_app.logger.warn('WARN')
    current_app.logger.info('INFO')
    current_app.logger.debug('DEBUG')


    return 'index_page'