#Essa daqui é a rota principal do nosso projeto, nosso redirecionamento pras páginas do app dependem exclusivamente dessa rota

from django.contrib import admin
from django.urls import path, include #Por padrão é necessário importar o include para incluir as rotas dos nossos apps.

urlpatterns = [
    path('admin/', admin.site.urls),
    
    #Views de Main
    path('', include('main.urls')),
    path("api/", include("main.api.urls")),
    
    #Views de Users
    path('users/', include('users.urls')),
    path("api-users/", include("users.api.urls")),

    # Views de Registro de Ponto
    path('registro-ponto/', include('registro_ponto.urls')),
    path('api-registro-ponto/', include('registro_ponto.api.urls')),
]
