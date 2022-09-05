from django.shortcuts import render
from django.views import View
from django.http.response import HttpResponseBadRequest
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse


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