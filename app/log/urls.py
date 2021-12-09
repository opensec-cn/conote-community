from django.urls import path, re_path

from . import views


app_name = 'log'
urlpatterns = [
    path('', views.IndexList.as_view(), name='index'),
    path('refresh/api/', views.RefreshApiKey.as_view(), name='refresh-apikey'),

    path('weblog/list/', views.WebLogList.as_view(), name='weblog-list'),
    path('weblog/<int:pk>/', views.WebLogDetail.as_view(), name='weblog-detail'),
    path('weblog/<int:pk>/delete/', views.WebLogDelete.as_view(), name='weblog-delete'),

    path('dnslog/list/', views.DNSLogList.as_view(), name='dnslog-list'),
    path('delete/', views.LogDelete.as_view(), name='log-delete'),

    path('note/list/', views.NoteList.as_view(), name='note-list'),
    re_path('^note/create/(?P<action>text|file|code|article)/$', views.NoteCreate.as_view(), name='note-create'),

    path('note/<int:pk>/delete/', views.NoteDelete.as_view(), name='note-delete'),
    path('note/<int:pk>/update/', views.NoteUpdate.as_view(), name='note-update'),
    path('note/<int:pk>/preview/', views.NotePreview.as_view(), name='note-preview'),

    path('shortdomain/list/', views.ShortDomainList.as_view(), name='shortdomain-list'),
    path('shortdomain/create/', views.ShortDomainCreate.as_view(), name='shortdomain-create'),
    path('shortdomain/<int:pk>/update/', views.ShortDomainUpdate.as_view(), name='shortdomain-update'),
    path('shortdomain/<int:pk>/delete/', views.ShortDomainDelete.as_view(), name='shortdomain-delete'),

    path('dns_record/', views.DNSRecordUpdate.as_view(), name='dns-record'),
]
