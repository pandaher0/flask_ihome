# coding:utf-8
# Author:hxj
import redis


class Config(object):
    SECRET_KEY = 'asdagfdahadgnhsddf'
    # 数据库连接
    SQLALCHEMY_DATABASE_URI = 'mysql://root:root@39.106.44.166:3306/flask_ihome'
    SQLALCHEMY_TRACK_MODIFICATIONS = True
    # redis配置
    REDIS_HOST = '39.106.44.166'
    REDIS_PORT = 6379
    # session设置
    SESSION_TYPE = 'redis'
    SESSION_REDIS = redis.StrictRedis(host=REDIS_HOST, port=REDIS_PORT)
    # session过期时间
    PERMANENT_SESSION_LIFETIME = 86400


class DevelopmentConfig(Config):
    DEBUG = True
    """开发环境"""
    pass


class ProductionConfig(Config):
    """生产环境"""
    pass


config_map = {
    'develop':DevelopmentConfig,
    'product':ProductionConfig
}