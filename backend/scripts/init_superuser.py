"""Initialize superuser script for Django."""
from apps.users.models import User
from django.conf import settings
import os


def run():
    """Create superuser if not exists."""
    username = os.getenv('ADMIN_USERNAME', 'admin')
    email = os.getenv('ADMIN_EMAIL', 'admin@example.com')
    password = os.getenv('ADMIN_PASSWORD', 'admin123')

    if not User.objects.filter(username=username).exists():
        User.objects.create_superuser(
            username=username,
            email=email,
            password=password
        )
        print(f'Superuser {username} created successfully.')
    else:
        print(f'Superuser {username} already exists.')
