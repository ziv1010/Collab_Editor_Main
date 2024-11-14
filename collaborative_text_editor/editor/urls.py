# editor/urls.py

from django.urls import path
from django.contrib.auth import views as auth_views
from . import views

urlpatterns = [
    path('register/', views.register, name='register'),
    path('login/', auth_views.LoginView.as_view(template_name='login.html'), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), name='logout'),
    path('', views.document_list, name='document_list'),
    path('document/new/', views.document_create, name='document_create'),
    path('document/<int:pk>/edit/', views.document_edit, name='document_edit'),
]
