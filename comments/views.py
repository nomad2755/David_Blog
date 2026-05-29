# Create your views here.
from django.core.exceptions import ValidationError
from django.http import HttpResponseRedirect, JsonResponse
from django.shortcuts import get_object_or_404
from django.views import View

from accounts.models import BlogUser
from blog.models import Article
from djangoblog.base_views import AuthenticatedFormView
from .forms import CommentForm
from .models import Comment, CommentReaction
from .utils import parse_mentions, get_unread_notifications_count, mark_notifications_as_read


class CommentPostView(AuthenticatedFormView):
    """
    评论提交视图

    使用 AuthenticatedFormView 基类，自动提供：
    - 登录验证（未登录用户会被重定向）
    - CSRF 保护
    """
    form_class = CommentForm
    template_name = 'blog/article_detail.html'

    def get(self, request, *args, **kwargs):
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)
        url = article.get_absolute_url()
        return HttpResponseRedirect(url + "#comments")

    def form_invalid(self, form):
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)

        return self.render_to_response({
            'form': form,
            'article': article
        })

    def form_valid(self, form):
        """提交的数据验证合法后的逻辑"""
        user = self.request.user
        author = BlogUser.objects.get(pk=user.pk)
        article_id = self.kwargs['article_id']
        article = get_object_or_404(Article, pk=article_id)

        if article.comment_status == 'c' or article.status == 'c':
            raise ValidationError("该文章评论已关闭.")
        comment = form.save(False)
        comment.article = article
        from djangoblog.utils import get_blog_setting
        settings = get_blog_setting()
        if not settings.comment_need_review:
            comment.is_enable = True
        comment.author = author

        if form.cleaned_data['parent_comment_id']:
            parent_comment = Comment.objects.get(
                pk=form.cleaned_data['parent_comment_id'])
            comment.parent_comment = parent_comment

        comment.save(True)

        # 处理@提及
        mentioned_users = parse_mentions(comment.body)
        if mentioned_users:
            comment.mentioned_users.set(mentioned_users)

        return HttpResponseRedirect(
            "%s#div-comment-%d" %
            (article.get_absolute_url(), comment.pk))


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
