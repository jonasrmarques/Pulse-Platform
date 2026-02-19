from django.urls import path
from .views import RegistroPontoView

urlpatterns = [
    path('', RegistroPontoView.as_view(), name='registro_ponto'),
]
