from django.shortcuts import render
from django.views import View
from django.http.response import HttpResponseBadRequest, JsonResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse
from utils.response_code import RETCODE
import logging
from random import randint
from libs.yuntongxun.sms import CCP

logger = logging.getLogger('django')


# Create your views here.
# 注册试图
class RegisterView(View):

    def get(self, request):

        return render(request, 'register.html')


# 图片验证码试图
class ImageCodeView(View):

    def get(self, request):
        """
        1. 接收前端传递过来的uuid
        2. 判断uuid是否获取到
        3. 通过调用captcha来生成图片验证码（图片二进制和图片内容）
        4. 将图片内容保存到redis中
            uuid作为一个key， 图片内容作为一个value 同时还需要设置一个时效
        5. 返回图片二进制
        :param request:
        :return:
        """

        uuid = request.GET.get('uuid')

        if uuid is None:
            return HttpResponseBadRequest('没有传递uuid')

        text, image = captcha.generate_captcha()

        redis_conn = get_redis_connection('default')
        redis_conn.setex('img:%s'%uuid, 300, text)

        return HttpResponse(image, content_type='image/jpeg')


# 短信验证码视图
class SmsCodeView(View):

    def get(self, request):
        """
        1. 接收参数
        2. 参数的验证
            2.1 参数是否齐全（mobile, image_code, uuid）
            2.2 图片验证码的验证：
                链接redis， 获取redis中的图片验证码；
                判断图片验证码是否存在；
                如果图片验证码未过期，我们获取到之后就可以删除图片验证码；
                比对图片验证码
        3. 生成短信验证码
        4. 保存短信验证码到redis中
        5. 发送短信
        6. 返回相应，前端开始计时
        :param request:
        :return:
        """

        mobile = request.GET.get('mobile')
        image_code = request.GET.get('image_code')
        uuid = request.GET.get('uuid')

        if not all([mobile, image_code, uuid]):
            return JsonResponse({'code': RETCODE.NECESSARYPARAMERR, 'errmsg': '缺少必传参数'})

        redis_conn = get_redis_connection('default')
        redis_image_code = redis_conn.get('img:%s'%uuid)

        if redis_image_code is None:
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg': '图形验证码失效'})

        try:
            redis_conn.delete('img:%s'%uuid)
        except Exception as e:
            logger.error(e)

        if image_code.lower() != redis_image_code.decode().lower():
            return JsonResponse({'code': RETCODE.IMAGECODEERR, 'errmsg':'输入图形验证码有误'})

        sms_code = '%06d'%randint(0, 999999)
        logger.info(sms_code)

        redis_conn.setex('sms:%s'%mobile, 300, sms_code)

        CCP().send_template_sms('1', mobile, [sms_code, '5'])

        return JsonResponse({'code': RETCODE.OK, 'errmsg': '发送短信成功'})

