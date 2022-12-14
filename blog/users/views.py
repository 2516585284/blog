import re

from django.shortcuts import render,redirect
from django.urls import reverse
from django.views import View
from django.http.response import HttpResponseBadRequest, JsonResponse
from libs.captcha.captcha import captcha
from django_redis import get_redis_connection
from django.http import HttpResponse
from utils.response_code import RETCODE
import logging
from random import randint
from libs.yuntongxun.sms import CCP
from users.models import User
from django.db import DatabaseError

logger = logging.getLogger('django')


# Create your views here.
# 注册试图
class RegisterView(View):

    def get(self, request):

        return render(request, 'register.html')

    def post(self, request):
        """
        1. 接收前端传递过来的参数(手机号，密码，确认密码，短信验证码)
        2. 验证参数
            2.1 验证参数是否齐全
            2.2 手机号格式是否正确
            2.3 密码是否符合格式
            2.4 密码和确认密码要一致
            2.5 短信验证码是否和redis中的一致
        3. 保存注册信息
        4. 返回响应，跳转到指定页面
        :param request:
        :return:
        """
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')

        if not all([mobile, password, password2, smscode]):
            return HttpResponseBadRequest('缺少必要的参数')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')

        if not re.match(r'^[0-9a-zA-z]{8,20}$', password):
            return HttpResponseBadRequest('请输入8-20位密码，密码是数字，字母')

        if password != password2:
            return HttpResponseBadRequest('两次密码不一致')

        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s'%mobile)

        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')

        if redis_sms_code.decode() != smscode:
            return HttpResponseBadRequest('短信验证码不一致')

        # 创建新用户并插入数据库
        try:
            # create_user()可以使用系统的方法来对密码进行加密
            user = User.objects.create_user(username=mobile, mobile=mobile, password=password)
        except DatabaseError as e:
            logger.error(e)
            return HttpResponseBadRequest('注册失败')

        from django.contrib.auth import login
        login(request, user)

        # return HttpResponse('注册成功，重定向到首页')
        # reverse（）可以通过namespace:name来获取到视图所对应的路由
        response = redirect(reverse('home:index'))

        response.set_cookie('is_login', True)
        response.set_cookie('username', user.username, 7*24*3600)

        return response


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


# 登录视图
class LoginView(View):

    def get(self, request):

        return render(request, 'login.html')

    def post(self, request):
        """
        1. 接收参数
        2. 验证参数
            手机号
            密码
        3. 用户认证登录
        4. 状态保持
        5. 根据用户选择的是否记住登录状态来进行判断
        6. 为了首页显示我们需要设置一些cookie信息
        7. 返回响应
        :param request:
        :return:
        """
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        remember = request.POST.get('remember')

        if not all([mobile, password]):
            return HttpResponseBadRequest()

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码不符合规则')

        # 采用系统自带的认证方法进行认证（如果用户名和密码正确，会返回user；如果用户名或密码不正确，会返回None）
        # 默认的认证方法是针对于username字段进行用户名的判断
        from django.contrib.auth import authenticate
        user = authenticate(mobile=mobile, password=password)

        if user is None:
            return HttpResponseBadRequest('用户名或密码错误')

        from django.contrib.auth import login
        login(request, user)

        # 根据next参数来进行页面的跳转
        next_page = request.GET.get('next')
        if next_page:
            response = redirect(next_page)
        else:

            response = redirect(reverse('home:index'))

        if remember != 'on':
            request.session.set_expiry(0)
            response.set_cookie('is_login', True)
            response.set_cookie('username', user.username, max_age=14*24*3600)
        else:
            request.session.set_expiry(None)
            response.set_cookie('is_login', True, max_age=14*24*3600)
            response.set_cookie('username', user.username, max_age=14*24*3600)

        return response


from django.contrib.auth import logout
class LogoutView(View):

    def get(self, request):
        """
        1. session数据清除
        2. 删除部分cookie数据
        3. 跳转到首页
        :param request:
        :return:
        """
        logout(request)

        response = redirect(reverse('home:index'))
        response.delete_cookie('is_login')

        return response


class ForgerPasswordView(View):

    def get(self, request):

        return render(request, 'forget_password.html')


    def post(self, request):
        """
        1.接收数据
        2.验证数据
            判断参数是否齐全
            手机号是否符合规则
            判断密码是否符合规则
            判断确认密码和密码是否一致
            判断短信验证码是否正确
        3.根据手机号进行用户信息的查询
        4.如果手机号查询出用户信息则进行用户密码的修改
        5.如果手机号没有查询出用户信息，则进行新用户的创建
        6.进行页面跳转，跳转到首页
        7.返回响应
        :param request:
        :return:
        """
        mobile = request.POST.get('mobile')
        password = request.POST.get('password')
        password2 = request.POST.get('password2')
        smscode = request.POST.get('sms_code')

        if not all([mobile, password, password2, smscode]):
            return HttpResponseBadRequest('参数不全')

        if not re.match(r'^1[3-9]\d{9}$', mobile):
            return HttpResponseBadRequest('手机号不符合规则')

        if not re.match(r'^[0-9a-zA-Z]{8,20}$', password):
            return HttpResponseBadRequest('密码不符合规则')

        if password != password2:
            return HttpResponseBadRequest('密码不一致')

        # 验证手机验证码
        redis_conn = get_redis_connection('default')
        redis_sms_code = redis_conn.get('sms:%s'%(mobile))

        if redis_sms_code is None:
            return HttpResponseBadRequest('短信验证码已过期')

        if redis_sms_code.decode() != smscode:
            return HttpResponseBadRequest('短信验证码错误')

        # 根据手机号查询用户
        try:
            user = User.objects.get(mobile=mobile)
        except User.DoesNotExist:
            # 注册一个新用户
            try:
                User.objects.create_user(username=mobile,mobile=mobile, password=password)
            except Exception:
                return HttpResponseBadRequest('修改失败，请稍后再试')

        else:
            # 修改用户密码
            user.set_password(password)
            user.save()

        response = redirect(reverse('users:login'))
        return response


from django.contrib.auth.mixins import LoginRequiredMixin
# 如果用户未登录的话，则会进行默认的跳转，默认的跳转链接是accounts/login/?next=/center/
class UserCenterView(LoginRequiredMixin, View):

    def get(self, request):
        # 获得登录用户的信息
        user = request.user
        # 组织获取用户的信息
        context = {
            'username': user.username,
            'mobile': user.mobile,
            'avatar': user.avatar.url if user.avatar else None,
            'user_desc': user.user_desc
        }

        return render(request, 'center.html', context)

    def post(self, request):

        user = request.user
        username = request.POST.get('username', user.username)
        avatar = request.FILES.get('avatar')
        user_desc = request.POST.get('desc', user.user_desc)

        try:
            user.username = username
            user.user_desc = user_desc
            if avatar:
                user.avatar = avatar
            user.save()
        except Exception as e:
            logger.error(e)
            return HttpResponseBadRequest('修改失败，请稍后再试')

        response = redirect(reverse('users:center'))

        response.set_cookie('username', user.username, max_age=14*24*3600)
        return response


from home.models import ArticleCategory, Article
class WriteBlogView(LoginRequiredMixin, View):

    def get(self, request):

        # 查询所有分类模型
        categories = ArticleCategory.objects.all()

        context = {
            'categories':categories
        }

        return render(request, 'write_blog.html', context=context)

    def post(self, request):

        avatar = request.FILES.get('avatar')
        title = request.POST.get('title')
        category_id = request.POST.get('category')
        tags = request.POST.get('tags')
        sumary = request.POST.get('sumary')
        content = request.POST.get('content')
        user = request.user

        if not all([avatar, title, category_id, sumary, content]):
            return HttpResponseBadRequest('参数不全')
        try:
            category=ArticleCategory.objects.get(id=category_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseBadRequest('没有此分类')

        try:
            article = Article.objects.create(
                author=user,
                avatar=avatar,
                title=title,
                category=category,
                tags=tags,
                sumary=sumary,
                content=content
            )
        except Exception as e:
            return HttpResponseBadRequest('发布失败，请稍后再试')

        return redirect(reverse('home:index'))
