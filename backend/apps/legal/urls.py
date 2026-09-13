from django.urls import path

from .documents import PRIVACY_POLICY, TERMS_OF_SERVICE
from .views import legal_page

urlpatterns = [
    path("privacy/", legal_page, {"document": PRIVACY_POLICY}, name="privacy_policy"),
    path("terms/", legal_page, {"document": TERMS_OF_SERVICE}, name="terms_of_service"),
]
