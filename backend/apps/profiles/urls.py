from django.urls import path

from . import views

urlpatterns = [
    path("users/<int:user_id>/", views.profile, name="profile"),
    path("users/<int:user_id>/avatar/", views.avatar, name="avatar"),
    path("settings/", views.account_settings, name="account_settings"),
    path("friends/", views.friends, name="friends"),
    path("friends/request/", views.friend_request, name="friend_request"),
    path("friends/<int:friendship_id>/accept/", views.friend_accept, name="friend_accept"),
    path("friends/<int:friendship_id>/end/", views.friend_end, name="friend_end"),
]
