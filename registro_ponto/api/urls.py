from django.urls import path
from .views import BaterPontoAPIView, DashboardResumoAPIView, PontoHojeAPIView, HistoricoPontosAPIView

urlpatterns = [
    path('bater-ponto/', BaterPontoAPIView.as_view(), name='bater_ponto_api'),
    path('ponto-hoje/', PontoHojeAPIView.as_view(), name='ponto_hoje_api'),
    path('historico/', HistoricoPontosAPIView.as_view(), name='historico-pontos'),
    path("dashboard/", DashboardResumoAPIView.as_view(), name="api_dashboard_resumo"),
]
