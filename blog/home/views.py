from django.shortcuts import render
from django.views import View
from django.http import HttpResponse
from home.models import ArticleCategory, Article
from django.http.response import HttpResponseNotFound

# Create your views here.

class IndexView(View):

    def get(self, request):

        categories = ArticleCategory.objects.all()
        cat_id = request.GET.get('cat_id', 1)

        try:
            category = ArticleCategory.objects.get(id=cat_id)
        except ArticleCategory.DoesNotExist:
            return HttpResponseNotFound('没有此分类')

        # 获取分页参数
        page_num = request.GET.get('page_num', 1)
        page_size = request.GET.get('page_size', 10)

        articles = Article.objects.filter(category=category)

        from django.core.paginator import Paginator, EmptyPage
        paginator = Paginator(articles, per_page=page_size)

        try:
            page_articles = paginator.page(page_num)
        except EmptyPage:
            return HttpResponseNotFound('empty page')

        total_page = paginator.num_pages

        context={
            'categories':categories,
            'category':category,
            'articles':page_articles,
            'page_num':page_num,
            'page_size':page_size,
            'total_page':total_page,
        }

        return render(request, 'index.html', context=context)
