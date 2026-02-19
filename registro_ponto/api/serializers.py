from rest_framework import serializers
from .models import RegistroPonto

class RegistroPontoSerializer(serializers.ModelSerializer):
    class Meta:
        model = RegistroPonto
        fields = ['id', 'usuario', 'data', 'horario_entrada', 'horario_saida', 'status']
        read_only_fields = ['id', 'usuario', 'data', 'status']