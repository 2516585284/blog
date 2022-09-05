# -*- coding:utf-8 -*-

from libs.yuntongxun.CCPRestSDK import REST
from ronglian_sms_sdk import SmsSDK
import json

# 说明：主账号，登陆云通讯网站后，可在"控制台-应用"中看到开发者主账号ACCOUNT SID
_accountSid = '8aaf0708827c8fd50182aae3496d08dd'

# 说明：主账号Token，登陆云通讯网站后，可在控制台-应用中看到开发者主账号AUTH TOKEN
_accountToken = 'ec6505ccaf244881817ef59c8cdf409e'

# 请使用管理控制台首页的APPID或自己创建应用的APPID
_appId = '8aaf0708827c8fd50182aae34a3f08e4'

# 说明：请求地址，生产环境配置成app.cloopen.com
_serverIP = 'sandboxapp.cloopen.com'

# 说明：请求端口 ，生产环境为8883
_serverPort = "8883"

# 说明：REST API版本号保持不变
_softVersion = '2013-12-26'

# 云通讯官方提供的发送短信代码实例
# # 发送模板短信
# # @param to 手机号码
# # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
# # @param $tempId 模板Id
#
# def sendTemplateSMS(to, datas, tempId):
#     # 初始化REST SDK
#     rest = REST(serverIP, serverPort, softVersion)
#     rest.setAccount(accountSid, accountToken)
#     rest.setAppId(appId)
#
#     result = rest.sendTemplateSMS(to, datas, tempId)
#     for k, v in result.iteritems():
#
#         if k == 'templateSMS':
#             for k, s in v.iteritems():
#                 print '%s:%s' % (k, s)
#         else:
#             print '%s:%s' % (k, v)


class CCP(object):
    """发送短信的辅助类"""

    def __new__(cls, *args, **kwargs):
        # 判断是否存在类属性_instance，_instance是类CCP的唯一对象，即单例
        if not hasattr(CCP, "_instance"):
            cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
            cls._instance.sdk = SmsSDK(_accountSid, _accountToken, _appId)

        return cls._instance

    def send_template_sms(self, tid, mobile, datas):
        """发送模板短信"""
        # @param to 手机号码
        # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
        # @param temp_id 模板Id
        result = self._instance.sdk.sendMessage(tid, mobile, datas)
        # 如果云通讯发送短信成功，返回的字典数据result中statuCode字段的值为"000000"
        result = json.loads(result)
        if result.get("statusCode") == "000000":
            # 返回0 表示发送短信成功
            return 0
        else:
            # 返回-1 表示发送失败
            return -1


if __name__ == '__main__':
    # ccp = CCP()
    # # 注意： 测试的短信模板编号为1
    # ccp.send_template_sms('18310820688', ['1234', 5], 1)

    sdk = SmsSDK(_accountSid, _accountToken, _appId)
    tid = '1'
    mobile = '18325537518'
    datas = ('1234', '5')
    resp = sdk.sendMessage(tid, mobile, datas)

    print(resp)



# class CCP(object):
#     """发送短信的辅助类"""
#
#     def __new__(cls, *args, **kwargs):
#         # 判断是否存在类属性_instance，_instance是类CCP的唯一对象，即单例
#         if not hasattr(CCP, "_instance"):
#             cls._instance = super(CCP, cls).__new__(cls, *args, **kwargs)
#             cls._instance.rest = REST(_serverIP, _serverPort, _softVersion)
#             cls._instance.rest.setAccount(_accountSid, _accountToken)
#             cls._instance.rest.setAppId(_appId)
#         return cls._instance
#
#     def send_template_sms(self, to, datas, temp_id):
#         """发送模板短信"""
#         # @param to 手机号码
#         # @param datas 内容数据 格式为数组 例如：{'12','34'}，如不需替换请填 ''
#         # @param temp_id 模板Id
#         result = self.rest.sendTemplateSMS(to, datas, temp_id)
#         # 如果云通讯发送短信成功，返回的字典数据result中statuCode字段的值为"000000"
#         if result.get("statusCode") == "000000":
#             # 返回0 表示发送短信成功
#             return 0
#         else:
#             # 返回-1 表示发送失败
#             return -1