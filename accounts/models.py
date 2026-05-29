from django.contrib.auth.models import AbstractUser
from django.db import models
from django.urls import reverse
from django.utils.timezone import now
from django.utils.translation import gettext_lazy as _
from djangoblog.utils import get_current_site


# Create your models here.

class BlogUser(AbstractUser):
    nickname = models.CharField(_('nick name'), max_length=100, blank=True)
    creation_time = models.DateTimeField(_('creation time'), default=now)
    last_modify_time = models.DateTimeField(_('last modify time'), default=now)
    source = models.CharField(_('create source'), max_length=100, blank=True)
    # 新增字段
    avatar = models.ImageField(
        _('avatar'),
        upload_to='avatars/%Y/%m/',
        blank=True,
        null=True,
        help_text=_('用户头像')
    )
    bio = models.TextField(
        _('bio'),
        max_length=500,
        blank=True,
        help_text=_('个人简介')
    )
    website = models.URLField(
        _('website'),
        blank=True,
        help_text=_('个人网站')
    )
    location = models.CharField(
        _('location'),
        max_length=100,
        blank=True,
        help_text=_('所在地')
    )
    github = models.CharField(
        _('GitHub'),
        max_length=100,
        blank=True,
        help_text=_('GitHub用户名')
    )
    twitter = models.CharField(
        _('Twitter'),
        max_length=100,
        blank=True,
        help_text=_('Twitter用户名')
    )
    # 关注关系
    following = models.ManyToManyField(
        'self',
        verbose_name=_('following'),
        blank=True,
        symmetrical=False,
        related_name='followers'
    )

    def get_absolute_url(self):
        return reverse(
            'blog:author_detail', kwargs={
                'author_name': self.username})

    def __str__(self):
        return self.email

    def get_full_url(self):
        site = get_current_site().domain
        url = "https://{site}{path}".format(site=site,
                                            path=self.get_absolute_url())
        return url

    def get_avatar_url(self):
        """获取头像URL"""
        if self.avatar:
            return self.avatar.url
        return None

    def get_display_name(self):
        """获取显示名称"""
        return self.nickname or self.username

    def follow(self, user):
        """关注用户"""
        if user != self:
            self.following.add(user)

    def unfollow(self, user):
        """取消关注"""
        self.following.remove(user)

    def is_following(self, user):
        """检查是否关注了某用户"""
        return self.following.filter(pk=user.pk).exists()

    def get_followers_count(self):
        """获取粉丝数"""
        return self.followers.count()

    def get_following_count(self):
        """获取关注数"""
        return self.following.count()

    class Meta:
        ordering = ['-id']
        verbose_name = _('user')
        verbose_name_plural = verbose_name
        get_latest_by = 'id'
