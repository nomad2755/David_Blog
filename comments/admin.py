from django.contrib import admin
from django.urls import reverse
from django.utils.html import format_html
from django.utils.translation import gettext_lazy as _

from .models import Comment, CommentReaction


def disable_commentstatus(modeladmin, request, queryset):
    queryset.update(is_enable=False)


def enable_commentstatus(modeladmin, request, queryset):
    queryset.update(is_enable=True)


disable_commentstatus.short_description = _('Disable comments')
enable_commentstatus.short_description = _('Enable comments')


class GuestCommentFilter(admin.SimpleListFilter):
    """按评论者类型筛选"""
    title = '评论者类型'
    parameter_name = 'commenter_type'

    def lookups(self, request, model_admin):
        return (
            ('guest', '游客评论'),
            ('registered', '注册用户评论'),
        )

    def queryset(self, request, queryset):
        if self.value() == 'guest':
            return queryset.filter(author__isnull=True)
        if self.value() == 'registered':
            return queryset.filter(author__isnull=False)
        return queryset


class CommentAdmin(admin.ModelAdmin):
    list_per_page = 20
    list_display = (
        'id',
        'body',
        'commenter_info',
        'link_to_article',
        'is_enable',
        'creation_time')
    list_display_links = ('id', 'body')
    list_filter = ('is_enable', GuestCommentFilter)
    exclude = ('creation_time', 'last_modify_time')
    actions = [disable_commentstatus, enable_commentstatus]
    raw_id_fields = ('author', 'article')
    search_fields = ('body', 'guest_name', 'guest_email')

    def commenter_info(self, obj):
        """显示评论者信息（兼容注册用户和游客）"""
        if obj.author:
            info = (obj.author._meta.app_label, obj.author._meta.model_name)
            link = reverse('admin:%s_%s_change' % info, args=(obj.author.id,))
            name = obj.author.nickname or obj.author.email
            return format_html(
                u'<a href="{}">{}</a> <span style="color:#888;font-size:11px">注册用户</span>',
                link, name)
        else:
            name = obj.guest_name or '匿名'
            email = obj.guest_email or ''
            website = obj.guest_website or ''
            parts = [f'<strong>{name}</strong>']
            if email:
                parts.append(f'<br><span style="color:#888;font-size:11px">📧 {email}</span>')
            if website:
                parts.append(f'<br><span style="color:#888;font-size:11px">🔗 {website}</span>')
            parts.append('<br><span style="color:#e67e22;font-size:11px">👤 游客</span>')
            return format_html(''.join(parts))

    def link_to_article(self, obj):
        info = (obj.article._meta.app_label, obj.article._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.article.id,))
        return format_html(
            u'<a href="%s">%s</a>' % (link, obj.article.title))

    commenter_info.short_description = '评论者'
    link_to_article.short_description = _('Article')

    def get_queryset(self, request):
        """默认按未审核优先排序"""
        qs = super().get_queryset(request)
        return qs.order_by('is_enable', '-creation_time')


class CommentReactionAdmin(admin.ModelAdmin):
    list_display = ('id', 'reaction_type', 'link_to_comment', 'link_to_user', 'created_at')
    list_display_links = ('id', 'reaction_type')
    list_filter = ('reaction_type', 'created_at')
    raw_id_fields = ('comment', 'user')
    search_fields = ('comment__body', 'user__username')
    date_hierarchy = 'created_at'

    def link_to_comment(self, obj):
        info = (obj.comment._meta.app_label, obj.comment._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.comment.id,))
        return format_html(
            u'<a href="%s">Comment #%s</a>' % (link, obj.comment.id))

    def link_to_user(self, obj):
        info = (obj.user._meta.app_label, obj.user._meta.model_name)
        link = reverse('admin:%s_%s_change' % info, args=(obj.user.id,))
        return format_html(
            u'<a href="%s">%s</a>' %
            (link, obj.user.nickname if obj.user.nickname else obj.user.username))

    link_to_comment.short_description = _('Comment')
    link_to_user.short_description = _('User')


admin.site.register(Comment, CommentAdmin)
admin.site.register(CommentReaction, CommentReactionAdmin)
