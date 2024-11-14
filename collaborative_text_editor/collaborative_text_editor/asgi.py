"""
ASGI config for collaborative_text_editor project.

It exposes the ASGI callable as a module-level variable named ``application``.

For more information on this file, see
https://docs.djangoproject.com/en/3.2/howto/deployment/asgi/
"""

# collaborative_text_editor/asgi.py

import os
from django.core.asgi import get_asgi_application
from channels.routing import ProtocolTypeRouter

os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'collaborative_text_editor.settings')

application = ProtocolTypeRouter({
    "http": get_asgi_application(),
    # WebSocket protocol will be added later
})
