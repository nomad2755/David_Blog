# Create your views here.
import logging

from django.contrib import messages
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404, render
from django.utils.decorators import method_decorator
from django.views import View
from django.views.decorators.csrf import csrf_protect

from accounts.models import BlogUser
from blog.models import Article
from .forms import CommentForm
from .models import Comment, CommentReaction
from .utils import parse_mentions, get_unread_notifications_count, mark_notifications_as_read

logger = logging.getLogger(__name__)


class CommentPostView(View):
    """
    评论提交视图（支持登录用户和游客评论）
    使用标准 POST + Redirect 模式，确保提交后有明确的成功反馈。
    """

    @method_decorator(csrf_protect)
    def dispatch(self, *args, **kwargs):
        return super().dispatch(*args, **kwargs)

    def get(self, request, article_id):
        article = get_object_or_404(Article, pk=article_id)
        return HttpResponseRedirect(article.get_absolute_url() + "#comments")

    def post(self, request, article_id):
        article = get_object_or_404(Article, pk=article_id)

        # 检查文章评论是否关闭
        if article.comment_status == 'c' or article.status == 'c':
            messages.error(request, '该文章评论已关闭。')
            return HttpResponseRedirect(article.get_absolute_url())

        form = CommentForm(request.POST)

        if not form.is_valid():
            # 表单验证失败，重新渲染页面
            context = {
                'form': form,
                'article': article,
                'page_title': article.title,
            }
            messages.error(request, '评论提交失败，请检查填写内容。')
            return render(request, 'blog/article_detail.html', context)

        comment = form.save(commit=False)
        comment.article = article

        is_authenticated = request.user.is_authenticated

        if is_authenticated:
            comment.author = BlogUser.objects.get(pk=request.user.pk)
            from djangoblog.utils import get_blog_setting
            blog_settings = get_blog_setting()
            if not blog_settings.comment_need_review:
                comment.is_enable = True
        else:
            # 游客验证
            guest_name = form.cleaned_data.get('guest_name', '').strip()
            guest_email = form.cleaned_data.get('guest_email', '').strip()

            if not guest_name:
                form.add_error('guest_name', '请输入昵称')
                messages.error(request, '请输入昵称。')
                return render(request, 'blog/article_detail.html', {
                    'form': form, 'article': article, 'page_title': article.title,
                })
            if not guest_email:
                form.add_error('guest_email', '请输入邮箱')
                messages.error(request, '请输入邮箱。')
                return render(request, 'blog/article_detail.html', {
                    'form': form, 'article': article, 'page_title': article.title,
                })

            comment.author = None
            comment.guest_name = guest_name
            comment.guest_email = guest_email
            comment.guest_website = form.cleaned_data.get('guest_website', '').strip()
            comment.is_enable = True

        # 处理父评论
        parent_id = form.cleaned_data.get('parent_comment_id')
        if parent_id:
            try:
                comment.parent_comment = Comment.objects.get(pk=parent_id)
            except Comment.DoesNotExist:
                pass

        comment.save()

        # 处理@提及
        if is_authenticated:
            mentioned_users = parse_mentions(comment.body)
            if mentioned_users:
                comment.mentioned_users.set(mentioned_users)

        # 成功提示并跳转到评论位置
        messages.success(request, '评论发表成功！')
        return HttpResponseRedirect(
            "%s#div-comment-%d" % (article.get_absolute_url(), comment.pk))


class CommentReactionView(View):
    """
    评论 Emoji 反应 API
    GET /comment/<comment_id>/react - 获取 reactions（公开）
    POST /comment/<comment_id>/react - 切换 reaction（需要登录）
    """

    def get(self, request, comment_id):
        """获取评论的 reactions 数据（公开访问）"""
        comment = get_object_or_404(Comment, id=comment_id, is_enable=True)

        # 传递用户信息，如果未登录则传递 None
        user = request.user if request.user.is_authenticated else None
        reactions_data = comment.get_reactions_summary(user)

        return JsonResponse({
            'success': True,
            'reactions': reactions_data
        })

    def post(self, request, comment_id):
        # POST 需要登录验证
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)
        # 获取评论（只有已启用的评论才能点赞）
        comment = get_object_or_404(Comment, id=comment_id, is_enable=True)

        # 获取 reaction 类型
        reaction_type = request.POST.get('reaction_type')

        # 验证 reaction_type 是否合法
        valid_reactions = [choice[0] for choice in CommentReaction.REACTION_CHOICES]
        if reaction_type not in valid_reactions:
            return JsonResponse({
                'error': 'Invalid reaction type'
            }, status=400)

        # 切换 reaction（如果已存在则删除，否则创建）
        reaction, created = CommentReaction.objects.get_or_create(
            comment=comment,
            user=request.user,
            reaction_type=reaction_type
        )

        if not created:
            # 已存在，删除它（取消点赞）
            reaction.delete()
            action = 'removed'
        else:
            action = 'added'

        # 返回该评论的所有 reactions 统计
        reactions_data = comment.get_reactions_summary(request.user)

        return JsonResponse({
            'success': True,
            'action': action,
            'reactions': reactions_data
        })


class CommentNotificationListView(View):
    """评论通知列表API"""

    def get(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)

        from .models import CommentNotification

        notifications = CommentNotification.objects.filter(
            recipient=request.user
        ).select_related('comment', 'comment__author', 'comment__article')[:20]

        notifications_data = []
        for notification in notifications:
            notifications_data.append({
                'id': notification.id,
                'type': notification.notification_type,
                'is_read': notification.is_read,
                'created_at': notification.created_at.isoformat(),
                'comment': {
                    'id': notification.comment.id,
                    'body': notification.comment.body[:100],
                    'author': notification.comment.author.username,
                    'article_title': notification.comment.article.title,
                    'article_url': notification.comment.article.get_absolute_url(),
                }
            })

        return JsonResponse({
            'success': True,
            'notifications': notifications_data,
            'unread_count': get_unread_notifications_count(request.user)
        })


class CommentNotificationMarkReadView(View):
    """标记通知为已读API"""

    def post(self, request):
        if not request.user.is_authenticated:
            return JsonResponse({
                'success': False,
                'error': 'Authentication required'
            }, status=401)

        notification_ids = request.POST.getlist('notification_ids')
        mark_notifications_as_read(request.user, notification_ids if notification_ids else None)

        return JsonResponse({
            'success': True,
            'unread_count': get_unread_notifications_count(request.user)
        })
