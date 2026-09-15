from django.urls import path

from . import views

urlpatterns = [
    path("login/verify/", views.login_verify, name="login_verify"),
    path("login/verify/cancel/", views.login_verify_cancel, name="login_verify_cancel"),
]
