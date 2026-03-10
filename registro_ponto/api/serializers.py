from rest_framework import serializers
from registro_ponto.models import RegistroPonto

class RegistroPontoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroPonto
        fields = ['id', 'usuario', 'data', 'horario_entrada', 'horario_saida', 'status']
        read_only_fields = ['id', 'usuario', 'data', 'status']


class DashboardResumoSerializer(serializers.Serializer):
    total_usuarios = serializers.IntegerField()
    registros_hoje = serializers.IntegerField()
    horas_extras = serializers.IntegerField()
    faltas = serializers.IntegerField()