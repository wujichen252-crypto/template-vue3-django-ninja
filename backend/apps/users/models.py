"""User model."""
from django.contrib.auth.models import AbstractBaseUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """User manager for creating users and superusers."""

    def create_user(self, username, email, password=None, **extra_fields):
        if not username:
            raise ValueError('用户名不能为空')
        if not email:
            raise ValueError('邮箱不能为空')

        email = self.normalize_email(email)
        user = self.model(username=username, email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, username, email, password=None, **extra_fields):
        extra_fields.setdefault('is_staff', True)
        extra_fields.setdefault('is_superuser', True)
        extra_fields.setdefault('status', 1)

        return self.create_user(username, email, password, **extra_fields)


class User(AbstractBaseUser):
    """Custom user model."""

    STATUS_NORMAL = 1
    STATUS_DISABLED = 0
    STATUS_CHOICES = [
        (STATUS_NORMAL, '正常'),
        (STATUS_DISABLED, '禁用'),
    ]

    username = models.CharField(max_length=32, unique=True, verbose_name='用户名')
    email = models.EmailField(max_length=128, unique=True, verbose_name='邮箱')
    avatar_url = models.URLField(max_length=500, blank=True, null=True, verbose_name='头像')
    status = models.PositiveSmallIntegerField(default=STATUS_NORMAL, choices=STATUS_CHOICES, verbose_name='状态')
    created_at = models.DateTimeField(auto_now_add=True, verbose_name='创建时间')
    updated_at = models.DateTimeField(auto_now=True, verbose_name='更新时间')
    is_staff = models.BooleanField(default=False, verbose_name='是否管理员')
    is_superuser = models.BooleanField(default=False, verbose_name='是否超级管理员')

    objects = UserManager()

    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']

    class Meta:
        db_table = 'users'
        verbose_name = '用户'
        verbose_name_plural = '用户'
        indexes = [
            models.Index(fields=['status', 'created_at'], name='idx_status_created_at'),
            models.Index(fields=['is_staff'], name='idx_is_staff'),
        ]

    def __str__(self):
        return self.username
