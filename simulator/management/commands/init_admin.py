from django.core.management.base import BaseCommand
from django.contrib.auth import get_user_model
from rest_framework.authtoken.models import Token
import os

class Command(BaseCommand):
    help = 'Creates a superuser and generates an API token automatically'

    def handle(self, *args, **options):
        User = get_user_model()
        username = os.environ.get('ADMIN_USER', 'admin')
        password = os.environ.get('ADMIN_PASSWORD', 'admin123')
        
        user, created = User.objects.get_or_create(username=username)
        if created:
            user.set_password(password)
            user.is_superuser = True
            user.is_staff = True
            user.save()
            self.stdout.write(self.style.SUCCESS(f'Successfully created admin user: {username}'))
        else:
            self.stdout.write(f'Admin user {username} already exists')

        token, _ = Token.objects.get_or_create(user=user)
        
        self.stdout.write(self.style.SUCCESS('='*40))
        self.stdout.write(self.style.SUCCESS(f'PRODUCTION TOKEN: {token.key}'))
        self.stdout.write(self.style.SUCCESS('='*40))
