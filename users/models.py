from django.contrib.auth.models import AbstractBaseUser, PermissionsMixin
from django.db import models
from .managers import UserManager
from enterprise.models import Cargos, Setores, TiposDeContrato

class User(AbstractBaseUser, PermissionsMixin):
    email = models.EmailField(unique=True)
    name = models.CharField(max_length=150)
    
    is_active = models.BooleanField(default=True)
    is_staff = models.BooleanField(default=False)
    
    date_joined = models.DateField(auto_now_add=True)

    #Informações de contrato
    cargo = models.ForeignKey(Cargos, on_delete=models.CASCADE, null=True, blank=True)
    setor = models.ForeignKey(Setores, on_delete=models.CASCADE, null=True, blank=True)
    tipo_contrato = models.ForeignKey(TiposDeContrato, on_delete=models.CASCADE, null=True, blank=True)
    data_admissao = models.DateField(null=True, blank=True)
    data_demissao = models.DateField(null=True, blank=True)
    horario_entrada = models.TimeField(null=True, blank=True)
    horario_saida = models.TimeField(null=True, blank=True)
    tempo_hora_extra = models.FloatField(null=True, blank=True)

    #Informações pessoais
    data_nascimento = models.DateField(null=True, blank=True)

    
    objects = UserManager()
    
    USERNAME_FIELD = "email"
    REQUIRED_FIELD = ["name"]
    
    def __str__(self):
        return self.email