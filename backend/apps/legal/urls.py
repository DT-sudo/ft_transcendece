from django.urls import path

from .views import legal_page

urlpatterns = [
    path("privacy/", legal_page, {"name": "privacy"}, name="privacy_policy"),
    path("terms/", legal_page, {"name": "terms"}, name="terms_of_service"),
]
