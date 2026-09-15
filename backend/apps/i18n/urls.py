from django.urls import path

from . import views

urlpatterns = [path("language/", views.set_language, name="set_language")]
