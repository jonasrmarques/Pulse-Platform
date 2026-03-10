from django.urls import path
from .views import DashboardRegistroPontoView, RegistroPontoView

urlpatterns = [
    path('', RegistroPontoView.as_view(), name='registro_ponto'),
    path("dashboard/", DashboardRegistroPontoView.as_view(), name="dashboard_registro_ponto"),
]
