import json

from django import forms
from django.contrib import admin
from django.contrib.auth import get_user_model
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

# Register your models here.
from .models import Article, Category, Tag, Links, SideBar, BlogSettings


class ArticleForm(forms.ModelForm):
    # body = forms.CharField(widget=AdminPagedownWidget())

    class Meta:
        model = Article
        fields = '__all__'


def makr_article_publish(modeladmin, request, queryset):
    queryset.update(status='p')


def draft_article(modeladmin, request, queryset):
    queryset.update(status='d')


def close_article_commentstatus(modeladmin, request, queryset):
    queryset.update(comment_status='c')


def open_article_commentstatus(modeladmin, request, queryset):
    queryset.update(comment_status='o')


makr_article_publish.short_description = _('Publish selected articles')
draft_article.short_description = _('Draft selected articles')
close_article_commentstatus.short_description = _('Close article comments')
open_article_commentstatus.short_description = _('Open article comments')


class ArticlelAdmin(admin.ModelAdmin):
    list_per_page = 20
    search_fields = ('body', 'title')
    form = ArticleForm

    class Media:
        js = ('admin/js/mdeditor_paste_image.js',)

    list_display = (
        'id',
        'title',
        'author',
        'link_to_category',
        'creation_time',
        'views',
        'status',
        'type',
        'article_order')
    list_display_links = ('id', 'title')
    list_filter = ('status', 'type', 'category')
    date_hierarchy = 'creation_time'
    filter_horizontal = ('tags',)
    exclude = ('creation_time', 'last_modify_time')
    view_on_site = True
    actions = [
        makr_article_publish,
        draft_article,
        close_article_commentstatus,
        open_article_commentstatus]
    raw_id_fields = ('author', 'category',)

    def link_to_category(self, obj):
        info = (obj.category._meta.app_label, obj.category._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.category.id,))
        return format_html(u'<a href="%s">%s</a>' % (link, obj.category.name))

    link_to_category.short_description = _('category')

    def get_form(self, request, obj=None, **kwargs):
        form = super(ArticlelAdmin, self).get_form(request, obj, **kwargs)
        form.base_fields['author'].queryset = get_user_model(
        ).objects.filter(is_superuser=True)
        return form

    def save_model(self, request, obj, form, change):
        super(ArticlelAdmin, self).save_model(request, obj, form, change)

    def get_view_on_site_url(self, obj=None):
        if obj:
            url = obj.get_full_url()
            return url
        else:
            from djangoblog.utils import get_current_site
            site = get_current_site().domain
            return site


class TagAdmin(admin.ModelAdmin):
    exclude = ('slug', 'last_mod_time', 'creation_time')


class CategoryAdmin(admin.ModelAdmin):
    list_display = ('name', 'parent_category', 'index')
    exclude = ('slug', 'last_mod_time', 'creation_time')


class LinksAdmin(admin.ModelAdmin):
    exclude = ('last_mod_time', 'creation_time')


class SideBarAdmin(admin.ModelAdmin):
    list_display = ('name', 'content', 'is_enable', 'sequence')
    exclude = ('last_mod_time', 'creation_time')


class BlogSettingsForm(forms.ModelForm):
    """站点配置表单 - 含JSON验证"""

    class Meta:
        model = BlogSettings
        fields = '__all__'
        widgets = {
            'resume_work_experience': forms.Textarea(attrs={
                'rows': 12,
                'style': 'font-family: monospace; font-size: 13px;',
            }),
            'resume_strengths': forms.Textarea(attrs={
                'rows': 4,
                'placeholder': '每行写一条优势，例如：\n5年Python开发经验，熟悉Django/Flask框架\n具备良好的代码规范和文档习惯\n有大型项目架构设计经验',
            }),
            'resume_job_expectation': forms.Textarea(attrs={
                'rows': 2,
                'placeholder': '如：Python开发工程师 | 深圳/上海 | 25-35K',
            }),
        }

    def clean_resume_work_experience(self):
        value = self.cleaned_data.get('resume_work_experience', '').strip()
        if not value:
            return value
        try:
            data = json.loads(value)
        except json.JSONDecodeError as e:
            raise forms.ValidationError(f'JSON格式错误: {e}')
        if not isinstance(data, list):
            raise forms.ValidationError('JSON格式错误：顶层必须是数组 [...]')
        for i, item in enumerate(data):
            if not isinstance(item, dict):
                raise forms.ValidationError(f'第{i+1}项必须是对象 {{...}}')
            for field in ('company', 'position', 'period'):
                if field not in item:
                    raise forms.ValidationError(f'第{i+1}项缺少必填字段: {field}')
            if 'projects' in item and not isinstance(item['projects'], list):
                raise forms.ValidationError(f'第{i+1}项的 projects 必须是数组')
        return value


class BlogSettingsAdmin(admin.ModelAdmin):
    """单例配置Admin - 直接跳转到编辑页面"""
    form = BlogSettingsForm

    fieldsets = (
        ('🌐 基本站点设置', {
            'fields': ('site_name', 'site_description', 'site_seo_description',
                       'site_keywords', 'color_scheme')
        }),
        ('📝 功能设置', {
            'fields': ('open_site_comment', 'comment_need_review',
                       'article_sub_length', 'sidebar_article_count',
                       'sidebar_comment_count', 'article_comment_count')
        }),
        ('👤 个人简历 — 基本信息', {
            'description': '填写个人基本信息，将展示在 About 页面。',
            'fields': ('resume_name', 'resume_avatar', 'resume_age',
                       'resume_years_experience', 'resume_education',
                       'resume_phone', 'resume_wechat')
        }),
        ('💼 个人简历 — 求职信息', {
            'fields': ('resume_job_status', 'resume_job_expectation',
                       'resume_strengths')
        }),
        ('🏢 个人简历 — 工作经历', {
            'description': (
                'JSON格式，顶层为数组，每项包含 company（公司）、position（职位）、'
                'period（时间段）和 projects（项目数组）。'
                '<br><details><summary style="cursor:pointer;color:#4f46e5;">'
                '点击查看示例 ▸</summary>'
                '<pre style="background:#f8f9fa;padding:12px;border-radius:6px;'
                'font-size:12px;overflow-x:auto;margin-top:8px;">'
                '[\n'
                '  {\n'
                '    "company": "XX科技有限公司",\n'
                '    "position": "高级Python工程师",\n'
                '    "period": "2022.06 - 至今",\n'
                '    "projects": [\n'
                '      {\n'
                '        "name": "智能客服系统",\n'
                '        "desc": "负责后端架构设计...",\n'
                '        "tech": "Python, Django, Redis, Celery"\n'
                '      }\n'
                '    ]\n'
                '  }\n'
                ']</pre></details>'
            ),
            'fields': ('resume_work_experience',)
        }),
        ('🚀 个人简历 — 最近项目经历', {
            'description': '支持Markdown格式，可以详细描述最近的项目经历、技术方案和成果。',
            'fields': ('resume_recent_projects',)
        }),
        ('🎨 Portfolio', {
            'classes': ('collapse',),
            'fields': ('portfolio_hero_title', 'portfolio_hero_subtitle',
                       'portfolio_skills', 'portfolio_experience',
                       'portfolio_education', 'portfolio_contact_email',
                       'portfolio_github', 'portfolio_linkedin')
        }),
        ('📊 广告与统计', {
            'classes': ('collapse',),
            'fields': ('show_google_adsense', 'google_adsense_codes',
                       'analytics_code')
        }),
        ('📋 备案信息', {
            'classes': ('collapse',),
            'fields': ('beian_code', 'show_gongan_code', 'gongan_beiancode')
        }),
        ('⚙️ 自定义代码', {
            'classes': ('collapse',),
            'fields': ('global_header', 'global_footer')
        }),
    )

    class Media:
        js = ('admin/js/resume_json_helper.js',)

    def has_add_permission(self, request):
        """如果已经存在配置，则禁止添加"""
        return not BlogSettings.objects.exists()

    def has_delete_permission(self, request, obj=None):
        """禁止删除配置"""
        return False

    def changelist_view(self, request, extra_context=None):
        """列表页直接跳转到编辑页面"""
        from django.http import HttpResponseRedirect
        obj = BlogSettings.objects.first()
        if obj:
            return HttpResponseRedirect(
                reverse('admin:blog_blogsettings_change', args=[obj.pk])
            )
        # 如果不存在配置，跳转到添加页面
        return HttpResponseRedirect(
            reverse('admin:blog_blogsettings_add')
        )

    def save_model(self, request, obj, form, change):
        """保存设置时清除缓存"""
        super().save_model(request, obj, form, change)
        # 确保缓存被清除
        from djangoblog.utils import cache
        cache.clear()
        self.message_user(request, '设置已保存，缓存已清除')
