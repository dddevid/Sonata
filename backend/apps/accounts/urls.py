from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from . import views

urlpatterns = [
    path('register/', views.register),
    path('login/', views.login),
    path('logout/', views.logout),
    path('refresh/', TokenRefreshView.as_view()),
    path('me/', views.me),
    path('me/update/', views.update_me),
    path('me/password/', views.change_password),
    path('server-info/', views.server_info),
    # Admin
    path('users/', views.list_users),
    path('users/create/', views.create_user),
    path('users/<int:user_id>/', views.manage_user),
    # Admin server settings
    path('settings/', views.server_settings),
    path('settings/regenerate-secret/', views.regenerate_secret_key),
    path('settings/regenerate-encryption/', views.regenerate_encryption_key),
]
