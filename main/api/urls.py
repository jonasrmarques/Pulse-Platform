from django.urls import path
from .views import LoginAPIView, LogoutAPIView, PulseChatbotView
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
)

urlpatterns = [
    path("login/", LoginAPIView.as_view(), name="api-login"),
    path("logout/", LogoutAPIView.as_view(), name="api-logout"),
    path('chatbot/', PulseChatbotView.as_view(), name='pulse_chatbot'),
]