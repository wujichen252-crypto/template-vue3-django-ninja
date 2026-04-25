# Generated initial migration for users app

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='User',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('password', models.CharField(max_length=128, verbose_name='密码')),
                ('last_login', models.DateTimeField(blank=True, null=True, verbose_name='最后登录时间')),
                ('username', models.CharField(max_length=32, unique=True, verbose_name='用户名')),
                ('email', models.EmailField(max_length=128, unique=True, verbose_name='邮箱')),
                ('avatar_url', models.URLField(blank=True, max_length=500, null=True, verbose_name='头像')),
                ('status', models.PositiveSmallIntegerField(choices=[(1, '正常'), (0, '禁用')], default=1, verbose_name='状态')),
                ('created_at', models.DateTimeField(auto_now_add=True, verbose_name='创建时间')),
                ('updated_at', models.DateTimeField(auto_now=True, verbose_name='更新时间')),
                ('is_staff', models.BooleanField(default=False, verbose_name='是否管理员')),
                ('is_superuser', models.BooleanField(default=False, verbose_name='是否超级管理员')),
            ],
            options={
                'verbose_name': '用户',
                'verbose_name_plural': '用户',
                'db_table': 'users',
            },
        ),
    ]
