# coding:utf-8
# Author:hxj
from ihome.tasks.main import celery_app
from ihome.libs.yuntongxun.sms import CCP


@celery_app.task
def send_sms(to, datas, tempID):
    ccp = CCP()
    ret = ccp.send_Templates_SMS(to, datas, tempID)
    return ret
