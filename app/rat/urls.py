from django.urls import path, re_path

from . import views


app_name = 'rat'
urlpatterns = [
    path('list/', views.ClientList.as_view(), name='rat-list'),
    path('detail/<str:pk>/', views.ClientManager.as_view(), name='rat-detail'),
    path('execute/', views.CommandExecute.as_view(), name='rat-execute'),
]
