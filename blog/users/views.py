from django.shortcuts import render
from django.views import View


# Create your views here.
# 注册试图
class RegisterView(View):

    def get(self, request):

        return render(request, 'register.html')

