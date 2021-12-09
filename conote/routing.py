from channels.auth import AuthMiddlewareStack
from channels.routing import ProtocolTypeRouter, URLRouter
from channels.security.websocket import OriginValidator
from django.core.asgi import get_asgi_application

from .urls import websocket_urlpatterns
from django.conf import settings


trust_origin = f'{settings.O_SERVER_SCHEME}://{settings.O_MAIN_DOMAIN}'

application = ProtocolTypeRouter({
    'http': get_asgi_application(),
    'websocket': OriginValidator(
        AuthMiddlewareStack(
            URLRouter(websocket_urlpatterns)
        ),
        [trust_origin]
    ),
})
