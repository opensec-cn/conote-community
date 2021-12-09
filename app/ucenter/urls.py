from django.urls import path

from . import views


app_name = 'ucenter'
urlpatterns = [
    path('login/', views.jump_for_login, name='login'),
    path('callback/', views.callback, name='callback'),
    path('check/', views.RegisterView.as_view(), name='check'),

    path('option/', views.OptionView.as_view(), name='option')
]
