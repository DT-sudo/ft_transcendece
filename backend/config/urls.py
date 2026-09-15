from django.urls import include, path

urlpatterns = [
    path("", include("apps.accounts.urls")),
    path("", include("apps.legal.urls")),
    path("", include("apps.notifications.urls")),
    path("", include("apps.privacy.urls")),
    path("", include("apps.profiles.urls")),
    path("", include("apps.scheduling.urls")),
    path("", include("apps.twofactor.urls")),
    path("", include("apps.i18n.urls")),
]
