# coding:utf-8
# Author:hxj

# 图片验证码过期时间：单位 秒
IMAGE_CODE_EXPIRED_TIME = 180

# 短信验证码过期时间：单位 秒
SMS_CODE_EXPIRED_TIME = 300

# 短信发送间隔 单位 秒
SEND_SMS_CODE_EXPIRED_TIME = 60

# 登录错误尝试次数
ACCESS_NUM = 3

# redis错误尝试记录有效期 单位 秒
ERR_ACCESS_EXPIRE_TIME = 600

# 七牛云域名地址
QINIU_URL_DOMAIN = 'http://pp9g22fmy.bkt.clouddn.com/'

# 城区信息缓存时间
AREA_INFO_REDIS_CACHE_EXPIRES = 7200

# 首页展示最多的房屋数量
HOME_PAGE_MAX_HOUSES = 5

# 首页房屋数据的Redis缓存时间，单位：秒
HOME_PAGE_DATA_REDIS_EXPIRES = 7200

# 房屋详情页展示的评论最大数
HOUSE_DETAIL_COMMENT_DISPLAY_COUNTS = 30

# 房屋详情页面数据Redis缓存时间，单位：秒
HOUSE_DETAIL_REDIS_EXPIRE_SECOND = 7200

# 房屋列表页面每页数据容量
HOUSE_LIST_PAGE_CAPACITY = 2

# 房屋列表页面页数缓存时间，单位秒
HOUES_LIST_PAGE_REDIS_CACHE_EXPIRES = 7200
