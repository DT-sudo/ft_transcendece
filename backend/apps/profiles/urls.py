from django.urls import path

from . import views

urlpatterns = [
    path("users/<int:user_id>/", views.profile, name="profile"),
    path("users/<int:user_id>/avatar/", views.avatar, name="avatar"),
    path("settings/", views.account_settings, name="account_settings"),
]
