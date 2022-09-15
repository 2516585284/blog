from django.db import models
from django.utils import timezone

# Create your models here.

class ArticleCategory(models.Model):
    title = models.CharField(max_length=100, blank=True)
    created = models.DateTimeField(default=timezone.now)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'tb_category'
        verbose_name = '类别管理'
        verbose_name_plural = verbose_name


from users.models import User
from django.utils import timezone
class Article(models.Model):
    """
    作者
    标题图
    标题
    分类
    标签
    摘要信息
    文章正文
    浏览量
    评论量
    文章的创建时间
    文章的修改时间
    """
    author = models.ForeignKey(User,on_delete=models.CASCADE)
    avatar = models.ImageField(upload_to='article/%Y%m%d/', blank=True)
    title = models.CharField(max_length=20, blank=True)
    category = models.ForeignKey(ArticleCategory, null=True, blank=True, on_delete=models.CASCADE,related_name='article')
    tags = models.CharField(max_length=20, blank=True)
    sumary = models.CharField(max_length=200, null=False, blank=False)
    content = models.TextField()
    total_views = models.PositiveSmallIntegerField(default=0)
    comments_count = models.PositiveSmallIntegerField(default=0)
    created = models.DateTimeField(default=timezone.now)
    updated = models.DateTimeField(auto_now=True)

    def __str__(self):
        return self.title

    class Meta:
        db_table = 'tb_article'
        ordering = ('-created',)
        verbose_name = '文章管理'
        verbose_name_plural = verbose_name
