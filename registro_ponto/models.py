from django.db import models
from django.conf import settings
from django.utils import timezone


class RegistroPonto(models.Model):

    STATUS_CHOICES = [
        ('horario_regular', 'Horário Regular'),
        ('hora_extra', 'Hora Extra'),
        ('horario_irregular', 'Horário Irregular'),
        ('falta', 'Falta'),
    ]

    usuario = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='registros_ponto'
    )

    data = models.DateField(default=timezone.now)

    horario_entrada = models.TimeField(null=True, blank=True)
    horario_saida = models.TimeField(null=True, blank=True)

    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default='horario_regular'
    )

    class Meta:
        unique_together = ('usuario', 'data')
        ordering = ['-data']

    def __str__(self):
        return f"{self.usuario.email} - {self.data}"
