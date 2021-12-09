from django.urls import path, re_path

from . import views


app_name = 'sandbox'
urlpatterns = [
    path('sandbox/list/', views.SandboxList.as_view(), name='sandbox-list'),
    path('sandbox/create/', views.SandboxCreate.as_view(), name='sandbox-create'),

    path('sandbox/<slug:pk>/delete/', views.SandboxDelete.as_view(), name='sandbox-delete'),
    path('sandbox/<slug:pk>/update/', views.SandboxUpdate.as_view(), name='sandbox-update'),
]
