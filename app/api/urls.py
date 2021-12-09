from django.urls import path

from . import views

app_name = 'api'
urlpatterns = [
    path('weblog/', views.WebLogList.as_view(), name='weblog-list'),
    path('weblog/<int:pk>/', views.WebLogDetailDestroy.as_view(), name='weblog-detail-delete'),

    path('dnslog/', views.DNSLogList.as_view(), name='dnslog-list'),
    path('dnslog/<int:pk>/', views.DNSLogDetailDestroy.as_view(), name='dnslog-detail-delete'),
]
