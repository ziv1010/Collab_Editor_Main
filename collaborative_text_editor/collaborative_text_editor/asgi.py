# collaborative_text_editor/asgi.py

import os

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collaborative_text_editor.settings')

import django
django.setup()

from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from django.core.asgi import get_asgi_application
from django.contrib.staticfiles.handlers import ASGIStaticFilesHandler  # Add this import
import editor.routing

application = ProtocolTypeRouter({
    "http": ASGIStaticFilesHandler(get_asgi_application()),  # Wrap with ASGIStaticFilesHandler
    "websocket": AuthMiddlewareStack(
        URLRouter(
            editor.routing.websocket_urlpatterns
        )
    ),
})
