from django.contrib.auth import get_user_model
from django.core.management.base import BaseCommand
from rest_framework_api_key.models import APIKey

User = get_user_model()


class Command(BaseCommand):
    help = 'Generate API keys for all users'

    def handle(self, *args, **options):
        users = User.objects.all()
        api_key, key = APIKey.objects.create_key(name="my-remote-service")
        self.stdout.write(f'API key generated for user: - {key}')
