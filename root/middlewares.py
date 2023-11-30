import re

from channels.db import database_sync_to_async
from channels.middleware import BaseMiddleware
from django.contrib.auth.models import AnonymousUser

class TokenAuthMiddleware(BaseMiddleware):
    # Do not add this to MIDDLEWARE in settings.py
    async def __call__(self, scope, receive, send):
        return await super().__call__(scope, receive, send)
