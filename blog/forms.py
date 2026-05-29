import logging

from django import forms
from django.utils.translation import gettext_lazy as _
from haystack.forms import SearchForm

from .models import Article, Category, Tag

logger = logging.getLogger(__name__)


class BlogSearchForm(SearchForm):
    querydata = forms.CharField(required=True)

    def search(self):
        datas = super(BlogSearchForm, self).search()
        if not self.is_valid():
            return self.no_query_found()

        if self.cleaned_data['querydata']:
            logger.info(self.cleaned_data['querydata'])
        return datas


TW_INPUT = ('w-full rounded-lg border border-border bg-white px-3 py-2 '
            'text-sm text-foreground placeholder:text-muted-foreground '
            'focus:outline-none focus:ring-2 focus:ring-primary/20 focus:border-primary/40 '
            'transition-colors')
TW_SELECT = TW_INPUT
TW_TEXTAREA = TW_INPUT.replace('rounded-lg', 'rounded-lg')
TW_FILE = ('block w-full text-sm text-foreground file:mr-4 file:py-2 file:px-4 '
           'file:rounded-lg file:border-0 file:text-sm file:font-medium '
           'file:bg-primary file:text-primary-foreground '
           'hover:file:bg-primary/90 file:cursor-pointer file:transition-colors')


class ArticleForm(forms.ModelForm):
    """文章编辑表单"""
    tags = forms.ModelMultipleChoiceField(
        queryset=Tag.objects.all(),
        widget=forms.CheckboxSelectMultiple,
        required=False,
        label=_('标签')
    )

    class Meta:
        model = Article
        fields = [
            'title', 'body', 'category', 'tags', 'status', 'comment_status',
            'type', 'show_toc', 'excerpt', 'featured_image',
            'seo_title', 'seo_description', 'seo_keywords'
        ]
        widgets = {
            'title': forms.TextInput(attrs={
                'class': TW_INPUT,
                'placeholder': _('请输入文章标题')
            }),
            'body': forms.Textarea(attrs={
                'class': TW_TEXTAREA + ' markdown-editor font-mono',
                'rows': 20,
                'placeholder': _('请输入文章内容（支持Markdown格式）')
            }),
            'category': forms.Select(attrs={
                'class': TW_SELECT
            }),
            'status': forms.Select(attrs={
                'class': TW_SELECT
            }),
            'comment_status': forms.Select(attrs={
                'class': TW_SELECT
            }),
            'type': forms.Select(attrs={
                'class': TW_SELECT
            }),
            'excerpt': forms.Textarea(attrs={
                'class': TW_TEXTAREA,
                'rows': 3,
                'placeholder': _('文章摘要，留空则自动截取')
            }),
            'featured_image': forms.ClearableFileInput(attrs={
                'class': TW_FILE
            }),
            'seo_title': forms.TextInput(attrs={
                'class': TW_INPUT,
                'placeholder': _('SEO标题，留空则使用文章标题')
            }),
            'seo_description': forms.Textarea(attrs={
                'class': TW_TEXTAREA,
                'rows': 2,
                'placeholder': _('SEO描述，留空则自动截取')
            }),
            'seo_keywords': forms.TextInput(attrs={
                'class': TW_INPUT,
                'placeholder': _('SEO关键词，用逗号分隔')
            }),
        }

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['category'].queryset = Category.objects.all()
        self.fields['category'].empty_label = _('请选择分类')

    def clean_title(self):
        title = self.cleaned_data.get('title')
        if not title:
            raise forms.ValidationError(_('标题不能为空'))
        return title

    def clean_body(self):
        body = self.cleaned_data.get('body')
        if not body:
            raise forms.ValidationError(_('内容不能为空'))
        return body
