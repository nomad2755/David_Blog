import logging
import os
import uuid

from django.conf import settings
from django.core.paginator import Paginator
from django.http import HttpResponse, HttpResponseForbidden
from django.shortcuts import get_object_or_404
from django.shortcuts import render
from django.templatetags.static import static
from django.utils import timezone
from django.utils.translation import gettext_lazy as _
from django.views.decorators.csrf import csrf_exempt
from django.views.generic.detail import DetailView
from django.views.generic.list import ListView
from haystack.views import SearchView

from blog.models import Article, Category, LinkShowType, Links, Tag
from comments.forms import CommentForm
from djangoblog.plugin_manage import hooks
from djangoblog.plugin_manage.hook_constants import ARTICLE_CONTENT_HOOK_NAME
from djangoblog.utils import cache, get_blog_setting, get_sha256
from djangoblog.mixins import (
    SlugCachedMixin,
    ArticleListMixin,
    OptimizedArticleQueryMixin,
    CachedListViewMixin,
    PageNumberMixin
)

logger = logging.getLogger(__name__)


class ArticleListView(CachedListViewMixin, PageNumberMixin, ListView):
    """
    文章列表视图基类（重构版）

    使用 Mixin 简化代码，消除重复逻辑
    子类只需实现 get_queryset_data() 和 get_queryset_cache_key() 方法
    """
    # template_name属性用于指定使用哪个模板进行渲染
    template_name = 'blog/article_index.html'

    # context_object_name属性用于给上下文变量取名（在模板中使用该名字）
    context_object_name = 'article_list'

    # 页面类型，分类目录或标签列表等
    page_type = ''
    paginate_by = settings.PAGINATE_BY
    page_kwarg = 'page'
    link_type = LinkShowType.L

    def get_view_cache_key(self):
        return self.request.get['pages']

    def get_context_data(self, **kwargs):
        kwargs['linktype'] = self.link_type
        return super(ArticleListView, self).get_context_data(**kwargs)


class IndexView(OptimizedArticleQueryMixin, ArticleListView):
    """
    首页视图（重构版）

    继承 OptimizedArticleQueryMixin 获得优化的查询方法
    """
    # 友情链接类型
    link_type = LinkShowType.I

    def get_queryset_data(self):
        # 使用 Mixin 提供的优化查询方法
        return self.get_optimized_article_queryset().filter(
            type='a', status='p'
        )

    def get_queryset_cache_key(self):
        return f'index_{self.page_number}'

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blog_setting = get_blog_setting()
        # 提供基础SEO数据
        context['seo_title'] = f"{blog_setting.site_name} | {blog_setting.site_description}"
        context['seo_description'] = blog_setting.site_seo_description
        context['seo_keywords'] = blog_setting.site_keywords
        return context


class ArticleDetailView(DetailView):
    '''
    文章详情页面
    '''
    template_name = 'blog/article_detail.html'
    model = Article
    pk_url_kwarg = 'article_id'
    context_object_name = "article"

    def get_context_data(self, **kwargs):
        comment_form = CommentForm()

        # 优化：直接查询父评论，减少数据库查询
        from comments.models import Comment
        parent_comments = Comment.objects.filter(
            article=self.object,
            parent_comment=None,
            is_enable=True
        ).select_related('author').prefetch_related(
            'comment_set__author'  # 预加载子评论及其作者
        ).order_by('-id')

        # 获取所有评论用于总数显示
        article_comments = self.object.comment_list()

        blog_setting = get_blog_setting()
        paginator = Paginator(parent_comments, blog_setting.article_comment_count)
        page = self.request.GET.get('comment_page', '1')
        if not page.isnumeric():
            page = 1
        else:
            page = int(page)
            if page < 1:
                page = 1
            if page > paginator.num_pages:
                page = paginator.num_pages

        p_comments = paginator.page(page)
        next_page = p_comments.next_page_number() if p_comments.has_next() else None
        prev_page = p_comments.previous_page_number() if p_comments.has_previous() else None

        if next_page:
            kwargs[
                'comment_next_page_url'] = self.object.get_absolute_url() + f'?comment_page={next_page}#commentlist-container'
        if prev_page:
            kwargs[
                'comment_prev_page_url'] = self.object.get_absolute_url() + f'?comment_page={prev_page}#commentlist-container'
        kwargs['form'] = comment_form
        kwargs['article_comments'] = article_comments
        kwargs['p_comments'] = p_comments
        kwargs['comment_count'] = len(
            article_comments) if article_comments else 0

        kwargs['next_article'] = self.object.next_article
        kwargs['prev_article'] = self.object.prev_article

        context = super(ArticleDetailView, self).get_context_data(**kwargs)
        article = self.object
        
        # 添加基础SEO数据
        blog_setting = get_blog_setting()
        from django.utils.html import strip_tags
        from django.utils.text import Truncator
        from djangoblog.utils import CommonMarkdown
        
        # 处理description：markdown -> HTML -> 纯文本，彻底去除格式
        html_content = CommonMarkdown.get_markdown(article.body)
        description = strip_tags(html_content)
        description = ' '.join(description.split())  # 规范化空白字符
        description = Truncator(description).chars(150, truncate='...')
        
        # 处理keywords：去除空格，用逗号分隔
        tags = [tag.name.strip() for tag in article.tags.all()]
        keywords = ", ".join(tags) if tags else blog_setting.site_keywords
        
        context['seo_title'] = f"{article.title} | {blog_setting.site_name}"
        context['seo_description'] = description
        context['seo_keywords'] = keywords
        
        # 触发文章详情加载钩子，让插件可以添加额外的上下文数据
        from djangoblog.plugin_manage.hook_constants import ARTICLE_DETAIL_LOAD
        hooks.run_action(ARTICLE_DETAIL_LOAD, article=article, context=context, request=self.request)
        
        # Action Hook, 通知插件"文章详情已获取"
        hooks.run_action('after_article_body_get', article=article, request=self.request)
        return context


class CategoryDetailView(SlugCachedMixin, OptimizedArticleQueryMixin, ArticleListView):
    """
    分类目录列表（重构版）

    使用 SlugCachedMixin 避免重复查询 Category
    使用 OptimizedArticleQueryMixin 优化文章查询
    """
    page_type = "分类目录归档"
    slug_url_kwarg = 'category_name'
    slug_model = Category

    def get_queryset_data(self):
        # 使用 Mixin 缓存的对象，只查询一次
        category = self.get_slug_object()
        categorynames = [c.name for c in category.get_sub_categorys()]

        return self.get_optimized_article_queryset().filter(
            category__name__in=categorynames, status='p'
        )

    def get_queryset_cache_key(self):
        # 复用缓存的对象，不再重复查询数据库
        category = self.get_slug_object()
        return f'category_list_{category.name}_{self.page_number}'

    def get_context_data(self, **kwargs):
        category = self.get_slug_object()
        categoryname = category.name

        try:
            categoryname = categoryname.split('/')[-1]
        except BaseException:
            pass

        kwargs['page_type'] = CategoryDetailView.page_type
        kwargs['tag_name'] = categoryname
        
        # 添加基础SEO数据
        blog_setting = get_blog_setting()
        article_count = self.get_queryset().count()
        kwargs['seo_title'] = f"{categoryname} | {blog_setting.site_name}"
        kwargs['seo_description'] = f"浏览 {categoryname} 分类下的所有文章，共 {article_count} 篇文章。"
        kwargs['seo_keywords'] = f"{categoryname}, {blog_setting.site_keywords}"
        
        return super(CategoryDetailView, self).get_context_data(**kwargs)


class AuthorDetailView(OptimizedArticleQueryMixin, ArticleListView):
    """
    作者详情页（重构版）

    使用 OptimizedArticleQueryMixin 优化文章查询
    """
    page_type = '作者文章归档'

    def get_queryset_cache_key(self):
        from uuslug import slugify
        author_name = slugify(self.kwargs['author_name'])
        return f'author_{author_name}_{self.page_number}'

    def get_queryset_data(self):
        author_name = self.kwargs['author_name']
        return self.get_optimized_article_queryset().filter(
            author__username=author_name, type='a', status='p'
        )

    def get_context_data(self, **kwargs):
        author_name = self.kwargs['author_name']
        kwargs['page_type'] = AuthorDetailView.page_type
        kwargs['tag_name'] = author_name
        
        # 添加基础SEO数据
        blog_setting = get_blog_setting()
        article_count = self.get_queryset().count()
        kwargs['seo_title'] = f"{author_name} 的文章 | {blog_setting.site_name}"
        kwargs['seo_description'] = f"浏览 {author_name} 发表的所有文章，共 {article_count} 篇。"
        kwargs['seo_keywords'] = f"{author_name}, {blog_setting.site_keywords}"
        
        return super(AuthorDetailView, self).get_context_data(**kwargs)


class TagDetailView(SlugCachedMixin, OptimizedArticleQueryMixin, ArticleListView):
    """
    标签列表页面（重构版）

    使用 SlugCachedMixin 避免重复查询 Tag
    使用 OptimizedArticleQueryMixin 优化文章查询
    """
    page_type = '分类标签归档'
    slug_url_kwarg = 'tag_name'
    slug_model = Tag

    def get_queryset_data(self):
        # 使用 Mixin 缓存的对象，只查询一次
        tag = self.get_slug_object()
        return self.get_optimized_article_queryset().filter(
            tags__name=tag.name, type='a', status='p'
        )

    def get_queryset_cache_key(self):
        # 复用缓存的对象，不再重复查询数据库
        tag = self.get_slug_object()
        return f'tag_{tag.name}_{self.page_number}'

    def get_context_data(self, **kwargs):
        tag = self.get_slug_object()
        kwargs['page_type'] = TagDetailView.page_type
        kwargs['tag_name'] = tag.name
        
        # 添加基础SEO数据
        blog_setting = get_blog_setting()
        article_count = self.get_queryset().count()
        kwargs['seo_title'] = f"{tag.name} | {blog_setting.site_name}"
        kwargs['seo_description'] = f"浏览所有关于 {tag.name} 的文章，共 {article_count} 篇内容。"
        kwargs['seo_keywords'] = f"{tag.name}, {blog_setting.site_keywords}"
        
        return super(TagDetailView, self).get_context_data(**kwargs)


class ArchivesView(OptimizedArticleQueryMixin, ArticleListView):
    """
    文章归档页面（重构版）

    使用 OptimizedArticleQueryMixin 优化文章查询
    """
    page_type = '文章归档'
    paginate_by = None
    page_kwarg = None
    template_name = 'blog/article_archives.html'

    def get_queryset_data(self):
        return self.get_optimized_article_queryset().filter(status='p')

    def get_queryset_cache_key(self):
        return 'archives'


class LinkListView(ListView):
    model = Links
    template_name = 'blog/links_list.html'

    def get_queryset(self):
        return Links.objects.filter(is_enable=True)


class EsSearchView(SearchView):
    def build_form(self, form_kwargs=None):
        """Override to enable highlighting"""
        if form_kwargs is None:
            form_kwargs = {}

        # Enable highlighting for search results
        from haystack.query import SearchQuerySet
        if self.searchqueryset is None:
            sqs = SearchQuerySet().highlight()
        else:
            sqs = self.searchqueryset.highlight()

        form_kwargs['searchqueryset'] = sqs
        return super().build_form(form_kwargs=form_kwargs)

    def get_context(self):
        paginator, page = self.build_page()
        context = {
            "query": self.query,
            "form": self.form,
            "page": page,
            "paginator": paginator,
            "suggestion": None,
        }
        if hasattr(self.results, "query") and self.results.query.backend.include_spelling:
            context["suggestion"] = self.results.query.get_spelling_suggestion()
        context.update(self.extra_context())

        return context


@csrf_exempt
def fileupload(request):
    """
    通用文件上传接口（保留向后兼容）
    注意：新功能请使用 EditorImageUploadView（/api/upload-image/）
    """
    if request.method == 'POST':
        sign = request.GET.get('sign', None)
        if not sign:
            return HttpResponseForbidden()
        if not sign == get_sha256(get_sha256(settings.SECRET_KEY)):
            return HttpResponseForbidden()
        response = []
        for filename in request.FILES:
            timestr = timezone.now().strftime('%Y/%m/%d')
            imgextensions = ['jpg', 'png', 'jpeg', 'bmp', 'gif', 'webp']
            fname = u''.join(str(filename))
            isimage = len([i for i in imgextensions if fname.find(i) >= 0]) > 0
            # 修复：使用 MEDIA_ROOT 替代 STATICFILES 保存上传文件
            subdir = "files" if not isimage else "image"
            base_dir = os.path.join(settings.MEDIA_ROOT, subdir, timestr)
            if not os.path.exists(base_dir):
                os.makedirs(base_dir)
            savepath = os.path.normpath(os.path.join(base_dir, f"{uuid.uuid4().hex}{os.path.splitext(filename)[-1]}"))
            if not savepath.startswith(os.path.normpath(base_dir)):
                return HttpResponse("only for post")
            with open(savepath, 'wb+') as wfile:
                for chunk in request.FILES[filename].chunks():
                    wfile.write(chunk)
            # 修复：生成 MEDIA_URL 路径而非 static() 路径
            rel_path = os.path.relpath(savepath, settings.MEDIA_ROOT)
            url = f"{settings.MEDIA_URL}{rel_path}"
            response.append(url)
        return HttpResponse(response)

    else:
        return HttpResponse("only for post")


# ===== 错误处理视图 =====
# 注意：这些函数保留是为了向后兼容
# 实际实现已经移动到 djangoblog.error_views
# 可以在 urls.py 中直接引用新的实现

from djangoblog.error_views import (
    page_not_found_view,
    server_error_view,
    permission_denied_view
)


def clean_cache_view(request):
    cache.clear()
    return HttpResponse('ok')


class AboutView(ListView):
    """
    个人介绍页面
    """
    template_name = 'blog/about.html'
    context_object_name = 'article_list'
    paginate_by = None  # 不分页

    def get_queryset(self):
        # 返回空查询集，因为个人介绍页面不需要文章列表
        return Article.objects.none()

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        blog_setting = get_blog_setting()

        context['seo_title'] = f"About | {blog_setting.site_name}"
        context['seo_description'] = f"Portfolio and blog of {blog_setting.site_name}"
        context['seo_keywords'] = "portfolio,about,skills,experience"

        # Parse skills JSON for template
        import json
        try:
            context['skills_list'] = json.loads(blog_setting.portfolio_skills) if blog_setting.portfolio_skills else []
        except (json.JSONDecodeError, TypeError):
            context['skills_list'] = []

        # Parse resume work experience JSON
        try:
            context['work_experience_list'] = json.loads(blog_setting.resume_work_experience) if blog_setting.resume_work_experience else []
        except (json.JSONDecodeError, TypeError):
            context['work_experience_list'] = []

        # Parse resume strengths into list
        if blog_setting.resume_strengths:
            context['strengths_list'] = [
                s.strip() for s in blog_setting.resume_strengths.strip().split('\n') if s.strip()
            ]
        else:
            context['strengths_list'] = []

        # Featured/pinned articles as projects
        context['featured_articles'] = Article.objects.filter(
            type='a', status='p', article_order__gt=0
        ).order_by('-article_order')[:6]

        return context


from django.contrib.auth.mixins import LoginRequiredMixin
from django.views import View
from django.views.generic import CreateView, UpdateView
from django.urls import reverse_lazy
from .forms import ArticleForm


class EditorImageUploadView(LoginRequiredMixin, View):
    """编辑器图片上传 API

    支持 Markdown 编辑器内的图片上传，返回 JSON 格式的图片 URL。
    接受 POST 请求，文件字段名为 'image'。
    """
    login_url = '/accounts/login/'

    def post(self, request):
        from django.http import JsonResponse

        image_file = request.FILES.get('image')
        if not image_file:
            return JsonResponse({'success': 0, 'message': '未获取到图片文件'}, status=400)

        # 验证文件类型
        allowed_types = ['image/jpeg', 'image/png', 'image/gif', 'image/webp', 'image/bmp', 'image/svg+xml']
        if image_file.content_type not in allowed_types:
            return JsonResponse({
                'success': 0,
                'message': f'不支持的图片格式: {image_file.content_type}'
            }, status=400)

        # 限制文件大小 (10MB)
        if image_file.size > 10 * 1024 * 1024:
            return JsonResponse({'success': 0, 'message': '图片大小不能超过 10MB'}, status=400)

        # 生成保存路径: uploads/editor/YYYY/MM/uuid.ext
        timestr = timezone.now().strftime('%Y/%m')
        ext = os.path.splitext(image_file.name)[1].lower()
        if ext not in ['.jpg', '.jpeg', '.png', '.gif', '.webp', '.bmp', '.svg']:
            ext = '.png'
        filename = f"{uuid.uuid4().hex}{ext}"
        rel_dir = os.path.join('editor', timestr)
        abs_dir = os.path.join(settings.MEDIA_ROOT, rel_dir)
        os.makedirs(abs_dir, exist_ok=True)

        savepath = os.path.normpath(os.path.join(abs_dir, filename))
        if not savepath.startswith(os.path.normpath(abs_dir)):
            return JsonResponse({'success': 0, 'message': '非法文件路径'}, status=400)

        with open(savepath, 'wb+') as f:
            for chunk in image_file.chunks():
                f.write(chunk)

        # 构建可访问的 URL
        url = f"{settings.MEDIA_URL}{rel_dir}/{filename}"

        return JsonResponse({
            'success': 1,
            'message': '上传成功',
            'url': url,
        })


class ArticleCreateView(LoginRequiredMixin, CreateView):
    """文章创建视图"""
    model = Article
    form_class = ArticleForm
    template_name = 'blog/article_edit.html'
    login_url = '/accounts/login/'

    def form_valid(self, form):
        form.instance.author = self.request.user
        return super().form_valid(form)

    def get_success_url(self):
        return reverse_lazy('blog:detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('创建文章')
        context['submit_text'] = _('发布文章')
        return context


class ArticleUpdateView(LoginRequiredMixin, UpdateView):
    """文章编辑视图"""
    model = Article
    form_class = ArticleForm
    template_name = 'blog/article_edit.html'
    login_url = '/accounts/login/'
    slug_field = 'slug'

    def get_queryset(self):
        # 只允许编辑自己的文章
        return Article.objects.filter(author=self.request.user)

    def get_success_url(self):
        return reverse_lazy('blog:detail', kwargs={'slug': self.object.slug})

    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)
        context['page_title'] = _('编辑文章')
        context['submit_text'] = _('保存修改')
        return context
