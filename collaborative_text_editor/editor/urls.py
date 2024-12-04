# FILE: ./editor/urls.py

from django.urls import path
from . import views
from django.contrib.auth import views as auth_views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.document_list, name='document_list'),
    path('document/new/', views.document_create, name='document_create'),
    path('document/<int:pk>/edit/', views.document_edit, name='document_edit'),
    path('document/<int:pk>/delete/', views.document_delete, name='document_delete'),
    path('document/<int:pk>/get_comments/', views.get_comments, name='get_comments'),
    
    # --- Version Control URL Patterns ---
    path('document/<int:pk>/save_version/', views.save_version, name='save_version'),
    path('document/<int:pk>/list_versions/', views.list_versions, name='list_versions'),
    path('document/<int:pk>/restore_version/', views.restore_version, name='restore_version'),
    path('document/<int:pk>/version/<int:version_id>/preview/', views.preview_version, name='preview_version'),
    path('document/<int:pk>/delete_version/', views.delete_version, name='delete_version'),
    path('document/<int:pk>/download/', views.download_as_doc, name='download_as_doc'),
]