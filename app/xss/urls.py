from django.urls import path

from . import views


app_name = 'xss'
urlpatterns = [
    path('project/', views.ProjectList.as_view(), name='project-create'),
    path('project/<int:pk>/', views.ProjectList.as_view(), name='project-detail'),
    path('project/<int:pk>/delete/', views.ProjectDelete.as_view(), name='project-delete'),
    path('victim/', views.VictimList.as_view(), name='victim-list'),
    path('victim/<int:pk>/', views.VictimDetail.as_view(), name='victim-detail'),
    path('victim/<int:pk>/delete/', views.VictimDelete.as_view(), name='victim-delete'),
]
