# collaborative_text_editor/asgi.py

import os
import django
from django.core.asgi import get_asgi_application  # Add this import
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.auth import AuthMiddlewareStack
import editor.routing

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collaborative_text_editor.settings')
django.setup()

application = ProtocolTypeRouter({
    "http": get_asgi_application(),  # Now this will be defined
    "websocket": AuthMiddlewareStack(
        URLRouter(
            editor.routing.websocket_urlpatterns
        )
    ),
})
