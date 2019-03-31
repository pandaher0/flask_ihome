# coding:utf-8

from CCPRestSDK import REST
import ConfigParser

# 主帐号
accountSid = '8a216da869c8398f0169d1948f4502f1'

# 主帐号Token
accountToken = '2ac9d673b2514a15b31eae4bceb50a00'

# 应用Id
appId = '8a216da869c8398f0169d1948fa702f8'

# 请求地址，格式如下，不需要写http://
serverIP = 'app.cloopen.com'

# 请求端口
serverPort = '8883'

# REST版本号
softVersion = '2013-12-26'


class CCP(object):
    # 保存实例属性
    instance = None

    def __new__(cls):
        if cls.instance is None:
            obj = super(CCP, cls).__new__(cls)
            # 初始化REST SDK
            obj.rest = REST(serverIP, serverPort, softVersion)
            obj.rest.setAccount(accountSid, accountToken)
            obj.rest.setAppId(appId)
            cls.instance = obj

        return cls.instance

    def send_Templates_SMS(self, to, datas, tempID):
        result = self.rest.sendTemplateSMS(to, datas, tempID)
        # for k, v in result.iteritems():
        #
        #     if k == 'templateSMS':
        #         for k, s in v.iteritems():
        #             print '%s:%s' % (k, s)
        #     else:
        #         print '%s:%s' % (k, v)
        status_code = result.get('statusCode')
        if status_code == '000000':
            return 0
        else:
            return -1


# 发送模板短信
# @param to 手机号码
# @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# @param $tempId 模板Id


# sendTemplateSMS(手机号码,内容数据,模板Id)
if __name__ == '__main__':
    ccp = CCP()
    ret = ccp.send_Templates_SMS("13366889573", ['1234', '5'], 1)
    print ret
