from django import forms
from django.forms import ModelForm
from django.utils.translation import gettext_lazy as _

from .models import Comment


class CommentForm(ModelForm):
    parent_comment_id = forms.IntegerField(
        widget=forms.HiddenInput, required=False)

    # 游客信息字段（登录用户不需要填写）
    guest_name = forms.CharField(
        max_length=50,
        required=False,
        label=_('昵称'),
        widget=forms.TextInput(attrs={
            'class': 'w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20',
            'placeholder': '你的昵称 *',
        })
    )
    guest_email = forms.EmailField(
        required=False,
        label=_('邮箱'),
        widget=forms.EmailInput(attrs={
            'class': 'w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20',
            'placeholder': '你的邮箱 *（不会公开显示）',
        })
    )
    guest_website = forms.CharField(
        required=False,
        label=_('网站'),
        widget=forms.URLInput(attrs={
            'class': 'w-full rounded-lg border border-border bg-background px-3.5 py-2.5 text-sm text-foreground placeholder:text-muted-foreground transition-colors focus:border-primary focus:outline-none focus:ring-2 focus:ring-primary/20',
            'placeholder': '你的网站（选填）',
        })
    )

    class Meta:
        model = Comment
        fields = ['body']

    def clean_guest_name(self):
        """游客昵称必填（仅未登录时）"""
        name = self.cleaned_data.get('guest_name', '').strip()
        return name

    def clean_guest_email(self):
        """游客邮箱必填（仅未登录时）"""
        email = self.cleaned_data.get('guest_email', '').strip()
        return email
