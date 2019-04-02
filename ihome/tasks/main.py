# coding:utf-8
# Author:hxj

from celery import Celery
from ihome.tasks import config

celery_app = Celery('ihome')
celery_app.config_from_object(config)

# 自动搜寻异步任务
celery_app.autodiscover_tasks(['ihome.tasks.sms'])
