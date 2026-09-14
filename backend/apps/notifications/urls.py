from django.urls import path

from . import views

urlpatterns = [
    path("notifications/", views.notification_list, name="notifications"),
    path("notifications/read/", views.mark_all_read, name="notifications_mark_read"),
    path("notifications/clear/", views.clear_all, name="notifications_clear"),
]
