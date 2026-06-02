import re
import logging

from django.utils.translation import gettext_lazy as _

from djangoblog.utils import get_current_site
from djangoblog.utils import send_email

logger = logging.getLogger(__name__)


def send_comment_email(comment):
    site = get_current_site().domain
    subject = _('Thanks for your comment')
    article_url = f"https://{site}{comment.article.get_absolute_url()}"

    # 给评论者发感谢邮件（仅注册用户有邮箱）
    author_email = comment.author.email if comment.author else comment.guest_email
    if author_email:
        html_content = _("""<p>Thank you very much for your comments on this site</p>
                    You can visit <a href="%(article_url)s" rel="bookmark">%(article_title)s</a>
                    to review your comments,
                    Thank you again!
                    <br />
                    If the link above cannot be opened, please copy this link to your browser.
                    %(article_url)s""") % {'article_url': article_url, 'article_title': comment.article.title}
        send_email([author_email], subject, html_content)

    try:
        if comment.parent_comment and comment.parent_comment.author:
            html_content = _("""Your comment on <a href="%(article_url)s" rel="bookmark">%(article_title)s</a><br/> has
                   received a reply. <br/> %(comment_body)s
                    <br/>
                    go check it out!
                     <br/>
                     If the link above cannot be opened, please copy this link to your browser.
                     %(article_url)s
                    """) % {'article_url': article_url, 'article_title': comment.article.title,
                            'comment_body': comment.parent_comment.body}
            tomail = comment.parent_comment.author.email
            send_email([tomail], subject, html_content)
    except Exception as e:
        logger.error(e)


def extract_mentioned_users(comment_body):
    """从评论内容中提取@提及的用户名"""
    # 匹配 @username 格式
    pattern = r'@(\w+)'
    usernames = re.findall(pattern, comment_body)
    return usernames


def send_comment_notification(recipient, comment, notification_type):
    """发送评论通知"""
    from .models import CommentNotification

    # 创建通知记录
    notification = CommentNotification.objects.create(
        recipient=recipient,
        comment=comment,
        notification_type=notification_type
    )

    # 发送邮件通知
    try:
        _send_notification_email(recipient, comment, notification_type)
    except Exception as e:
        logger.error(f"Failed to send notification email: {e}")

    return notification


def _send_notification_email(recipient, comment, notification_type):
    """发送通知邮件"""
    site = get_current_site().domain
    article_url = f"https://{site}{comment.article.get_absolute_url()}"

    subject_map = {
        'article_comment': _('New comment on your article'),
        'reply': _('New reply to your comment'),
        'mention': _('You were mentioned in a comment'),
    }

    subject = subject_map.get(notification_type, _('New comment notification'))

    html_content = _("""
    <p>Dear %(username)s,</p>

    <p>%(message)s</p>

    <p><strong>Article:</strong> %(article_title)s</p>
    <p><strong>Comment:</strong> %(comment_body)s</p>
    <p><strong>Author:</strong> %(comment_author)s</p>

    <p><a href="%(article_url)s">View comment</a></p>

    <p>If the link above cannot be opened, please copy this link to your browser:<br/>
    %(article_url)s</p>
    """) % {
        'username': recipient.username,
        'message': _get_notification_message(notification_type, comment),
        'article_title': comment.article.title,
        'comment_body': comment.body[:100] + '...' if len(comment.body) > 100 else comment.body,
        'comment_author': comment.author.username,
        'article_url': article_url,
    }

    send_email([recipient.email], subject, html_content)


def _get_notification_message(notification_type, comment):
    """获取通知消息"""
    author_name = comment.display_name
    messages = {
        'article_comment': _('%(author)s commented on your article "%(title)s"') % {
            'author': author_name,
            'title': comment.article.title
        },
        'reply': _('%(author)s replied to your comment') % {
            'author': author_name
        },
        'mention': _('%(author)s mentioned you in a comment') % {
            'author': author_name
        },
    }
    return messages.get(notification_type, _('New comment notification'))


def get_unread_notifications_count(user):
    """获取用户未读通知数量"""
    from .models import CommentNotification
    return CommentNotification.objects.filter(
        recipient=user,
        is_read=False
    ).count()


def mark_notifications_as_read(user, notification_ids=None):
    """标记通知为已读"""
    from .models import CommentNotification

    queryset = CommentNotification.objects.filter(
        recipient=user,
        is_read=False
    )

    if notification_ids:
        queryset = queryset.filter(id__in=notification_ids)

    queryset.update(is_read=True)


def parse_mentions(comment_body):
    """解析评论中的@提及"""
    from accounts.models import BlogUser

    usernames = extract_mentioned_users(comment_body)
    mentioned_users = []

    for username in usernames:
        try:
            user = BlogUser.objects.get(username=username)
            mentioned_users.append(user)
        except BlogUser.DoesNotExist:
            continue

    return mentioned_users
