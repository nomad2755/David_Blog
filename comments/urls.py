from django.urls import path

from . import views

app_name = "comments"
urlpatterns = [
    path(
        'article/<int:article_id>/postcomment',
        views.CommentPostView.as_view(),
        name='postcomment'),
    path(
        'comment/<int:comment_id>/react',
        views.CommentReactionView.as_view(),
        name='comment_react'),
    path(
        'notifications/',
        views.CommentNotificationListView.as_view(),
        name='notifications'),
    path(
        'notifications/mark-read/',
        views.CommentNotificationMarkReadView.as_view(),
        name='notifications_mark_read'),
]
