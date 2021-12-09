from django.urls import path, re_path

from . import views


app_name = 'disposable_email'
urlpatterns = [
    path('', views.EmailList.as_view(), name='list'),
    path('<int:pk>/', views.EmailDetail.as_view(), name='detail'),
    path('<int:pk>/download/', views.EmailDownload.as_view(), name='download'),
    path('<int:pk>/delete/', views.EmailDelete.as_view(), name='delete'),
    path('flush/', views.EmailFlush.as_view(), name='flush'),
    path('<int:pk>/box/delete/', views.BoxDelete.as_view(), name='box-delete'),
    path('generate/', views.EmailGenerate.as_view(), name='generate'),
]
