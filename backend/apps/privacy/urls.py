from django.urls import path

from . import views

urlpatterns = [
    path("privacy/my-data/", views.privacy_center, name="privacy_center"),
    path("privacy/my-data/export/", views.export_my_data, name="privacy_export_data"),
    path("privacy/my-data/delete/", views.delete_my_account, name="privacy_delete_account"),
]
