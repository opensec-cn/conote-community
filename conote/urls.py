"""conote URL Configuration

The `urlpatterns` list routes URLs to views. For more information please see:
    https://docs.djangoproject.com/en/1.11/topics/http/urls/
Examples:
Function views
    1. Add an import:  from my_app import views
    2. Add a URL to urlpatterns:  url(r'^$', views.home, name='home')
Class-based views
    1. Add an import:  from other_app.views import Home
    2. Add a URL to urlpatterns:  url(r'^$', Home.as_view(), name='home')
Including another URLconf
    1. Import the include() function: from django.conf.urls import url, include
    2. Add a URL to urlpatterns:  url(r'^blog/', include('blog.urls'))
"""
from django.urls import path, include
from django.contrib import admin

from app.rat import consumers

urlpatterns = [
    path('admin/', admin.site.urls),
    path('', include('app.log.urls', namespace='log')),

    path('auth/', include('app.ucenter.urls', namespace='auth')),
    path('xss/', include('app.xss.urls', namespace='xss')),
    path('sandbox/', include('app.sandbox.urls', namespace='sandbox')),
    path('api/', include('app.api.urls', namespace='api')),
    path('disposable_email/', include('app.disposable_email.urls', namespace='email')),
    path('rat/', include('app.rat.urls', namespace='rat'))
]

websocket_urlpatterns = [
    path('ws/rat/<str:serid>/', consumers.RatConsumer.as_asgi()),
]
