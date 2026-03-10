from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.utils import timezone
from registro_ponto.api.serializers import DashboardResumoSerializer
from registro_ponto.models import RegistroPonto
from registro_ponto.utils import calcular_horas_trabalhadas
from datetime import datetime, timedelta
import calendar
from django.contrib.auth import get_user_model
from django.db.models import Count


User = get_user_model()

class BaterPontoAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):

        usuario = request.user
        hoje = timezone.localtime().date()
        agora = timezone.localtime().time().replace(microsecond=0)


        ponto, created = RegistroPonto.objects.get_or_create(
            usuario=usuario,
            data=hoje
        )

        if not ponto.horario_entrada:
            ponto.horario_entrada = agora
        elif not ponto.horario_saida:
            ponto.horario_saida = agora
        else:
            return Response({"detail": "Ponto já finalizado hoje."})

        ponto.save()

        return Response({
            "usuario": usuario.email,
            "data": ponto.data,
            "horario_entrada": ponto.horario_entrada,
            "horario_saida": ponto.horario_saida,
            "status": ponto.get_status_display()
        })

class PontoHojeAPIView(APIView):
    permission_classes = [IsAuthenticated]

    def get(self, request):
        usuario = request.user
        hoje = timezone.localtime().date()

        ponto = RegistroPonto.objects.filter(
            usuario=usuario,
            data=hoje
        ).first()

        if not ponto:
            return Response({
                "existe": False
            })

        # Formata os horários para exibição
        horario_entrada = ponto.horario_entrada.strftime("%H:%M") if ponto.horario_entrada else None
        horario_saida = ponto.horario_saida.strftime("%H:%M") if ponto.horario_saida else None
        
        # Calcula o total de horas trabalhadas
        horas_trabalhadas = calcular_horas_trabalhadas(
            ponto.horario_entrada, 
            ponto.horario_saida
        ) if ponto.horario_entrada and ponto.horario_saida else None

        return Response({
            "existe": True,
            "horario_entrada": horario_entrada,
            "horario_saida": horario_saida,
            "horas_trabalhadas": horas_trabalhadas,
            "status": ponto.get_status_display()
        })
    
class HistoricoPontosAPIView(APIView):
    permission_classes = [IsAuthenticated]
    
    def get(self, request):
        usuario = request.user
        tipo = request.GET.get('tipo', 'mensal')
        
        if tipo == 'mensal':
            return self._consulta_mensal(usuario, request)
        elif tipo == 'anual':
            return self._consulta_anual(usuario, request)
        elif tipo == 'detalhe':
            return self._consulta_detalhe(usuario, request)
        elif tipo == 'periodo':
            return self._consulta_periodo(usuario, request)
        elif tipo == 'resumo':
            return self._consulta_resumo(usuario, request)
        else:
            return Response({
                'erro': 'Tipo de consulta inválido. Use: mensal, anual, detalhe, periodo ou resumo'
            }, status=400)
    
    def _consulta_mensal(self, usuario, request):
        mes = request.GET.get('mes')
        ano = request.GET.get('ano')
        
        if not mes or not ano:
            hoje = timezone.now()
            mes = hoje.month
            ano = hoje.year
        else:
            try:
                mes = int(mes)
                ano = int(ano)
            except ValueError:
                return Response({'erro': 'Mês e ano devem ser números válidos'}, status=400)
        
        if mes < 1 or mes > 12:
            return Response({'erro': 'Mês inválido'}, status=400)
        
        registros = RegistroPonto.objects.filter(
            usuario=usuario,
            data__year=ano,
            data__month=mes
        ).order_by('data')
        
        registros_list = []
        total_minutos = 0
        dias_com_registro = 0
        
        for registro in registros:
            dados_registro = self._formatar_registro(registro)
            if dados_registro['minutos_trabalhados']:
                total_minutos += dados_registro['minutos_trabalhados']
                dias_com_registro += 1
            registros_list.append(dados_registro)
        
        dias_sem_registro = self._identificar_dias_sem_registro(ano, mes, registros)
        
        stats = self._calcular_estatisticas(total_minutos, dias_com_registro, len(registros_list))
        
        return Response({
            'tipo': 'mensal',
            'mes': mes,
            'ano': ano,
            'nome_mes': self._get_nome_mes(mes),
            'total_registros': len(registros_list),
            'dias_com_registro': dias_com_registro,
            'dias_sem_registro': dias_sem_registro,
            'estatisticas': stats,
            'registros': registros_list,
            'primeiro_dia': f"01/{mes:02d}/{ano}",
            'ultimo_dia': f"{calendar.monthrange(ano, mes)[1]:02d}/{mes:02d}/{ano}"
        })
    
    def _consulta_anual(self, usuario, request):
        ano = request.GET.get('ano')
        
        if not ano:
            ano = timezone.now().year
        else:
            try:
                ano = int(ano)
            except ValueError:
                return Response({'erro': 'Ano inválido'}, status=400)
        
        registros = RegistroPonto.objects.filter(
            usuario=usuario,
            data__year=ano
        ).order_by('data')
        
        resumo_mensal = []
        total_anual_minutos = 0
        total_dias_ano = 0
        
        for mes in range(1, 13):
            registros_mes = [r for r in registros if r.data.month == mes]
            
            if registros_mes:
                minutos_mes = 0
                for reg in registros_mes:
                    if reg.horario_entrada and reg.horario_saida:
                        minutos_mes += self._calcular_minutos_trabalhados(reg)
                
                total_anual_minutos += minutos_mes
                total_dias_ano += len(registros_mes)
                
                resumo_mensal.append({
                    'mes': mes,
                    'nome_mes': self._get_nome_mes(mes),
                    'dias_trabalhados': len(registros_mes),
                    'total_horas': self._formatar_minutos(minutos_mes),
                    'minutos': minutos_mes
                })
            else:
                resumo_mensal.append({
                    'mes': mes,
                    'nome_mes': self._get_nome_mes(mes),
                    'dias_trabalhados': 0,
                    'total_horas': '00:00',
                    'minutos': 0
                })
        
        dias_semana = self._calcular_dias_semana(registros)
        
        return Response({
            'tipo': 'anual',
            'ano': ano,
            'total_anual': self._formatar_minutos(total_anual_minutos),
            'total_minutos': total_anual_minutos,
            'total_dias_trabalhados': total_dias_ano,
            'media_mensal': self._formatar_minutos(total_anual_minutos // 12) if total_anual_minutos > 0 else '00:00',
            'media_diaria': self._formatar_minutos(total_anual_minutos // total_dias_ano) if total_dias_ano > 0 else '00:00',
            'resumo_mensal': resumo_mensal,
            'distribuicao_dias_semana': dias_semana
        })
    
    def _consulta_detalhe(self, usuario, request):
        registro_id = request.GET.get('registro_id')
        
        if not registro_id:
            return Response({'erro': 'ID do registro é obrigatório'}, status=400)
        
        try:
            registro = RegistroPonto.objects.get(id=registro_id, usuario=usuario)
        except RegistroPonto.DoesNotExist:
            return Response({'erro': 'Registro não encontrado'}, status=404)
        
        return Response({
            'tipo': 'detalhe',
            'registro': self._formatar_registro_detalhado(registro)
        })
    
    def _consulta_periodo(self, usuario, request):
        data_inicio = request.GET.get('data_inicio')
        data_fim = request.GET.get('data_fim')
        
        if not data_inicio or not data_fim:
            return Response({'erro': 'Datas de início e fim são obrigatórias'}, status=400)
        
        try:
            data_inicio = datetime.strptime(data_inicio, '%Y-%m-%d').date()
            data_fim = datetime.strptime(data_fim, '%Y-%m-%d').date()
        except ValueError:
            return Response({'erro': 'Formato de data inválido. Use YYYY-MM-DD'}, status=400)
        
        if data_inicio > data_fim:
            return Response({'erro': 'Data início não pode ser maior que data fim'}, status=400)
        
        registros = RegistroPonto.objects.filter(
            usuario=usuario,
            data__gte=data_inicio,
            data__lte=data_fim
        ).order_by('data')
        
        registros_list = []
        total_minutos = 0
        
        for registro in registros:
            dados = self._formatar_registro(registro)
            if dados['minutos_trabalhados']:
                total_minutos += dados['minutos_trabalhados']
            registros_list.append(dados)
        
        return Response({
            'tipo': 'periodo',
            'data_inicio': data_inicio.strftime('%d/%m/%Y'),
            'data_fim': data_fim.strftime('%d/%m/%Y'),
            'total_registros': len(registros_list),
            'total_horas': self._formatar_minutos(total_minutos),
            'total_minutos': total_minutos,
            'media_diaria': self._formatar_minutos(total_minutos // len(registros_list)) if registros_list else '00:00',
            'registros': registros_list
        })
    
    def _consulta_resumo(self, usuario, request):
        hoje = timezone.now().date()
        
        registros_mes = RegistroPonto.objects.filter(
            usuario=usuario,
            data__year=hoje.year,
            data__month=hoje.month
        )
        
        total_minutos_mes = 0
        for reg in registros_mes:
            if reg.horario_entrada and reg.horario_saida:
                total_minutos_mes += self._calcular_minutos_trabalhados(reg)
        
        ultimos_registros = RegistroPonto.objects.filter(
            usuario=usuario
        ).order_by('-data', '-horario_entrada')[:5]
        
        return Response({
            'tipo': 'resumo',
            'mes_atual': {
                'nome': self._get_nome_mes(hoje.month),
                'ano': hoje.year,
                'dias_trabalhados': registros_mes.count(),
                'total_horas': self._formatar_minutos(total_minutos_mes),
                'progresso': (registros_mes.count() / 22) * 100 if registros_mes.count() > 0 else 0
            },
            'ultimos_registros': [self._formatar_registro(r) for r in ultimos_registros],
            'tem_ponto_aberto': registros_mes.filter(horario_saida__isnull=True).exists()
        })
    
    def _calcular_minutos_trabalhados(self, registro):
        """Calcula minutos trabalhados combinando data e hora"""
        if not registro.horario_entrada or not registro.horario_saida:
            return 0
        
        entrada = datetime.combine(registro.data, registro.horario_entrada)
        saida = datetime.combine(registro.data, registro.horario_saida)
        
        if saida < entrada:
            saida = saida + timedelta(days=1)
        
        delta = saida - entrada
        return int(delta.total_seconds() / 60)
    
    def _formatar_registro(self, registro):
        horario_entrada = registro.horario_entrada.strftime("%H:%M") if registro.horario_entrada else None
        horario_saida = registro.horario_saida.strftime("%H:%M") if registro.horario_saida else None
        
        minutos_trabalhados = self._calcular_minutos_trabalhados(registro)
        horas_trabalhadas = self._formatar_minutos(minutos_trabalhados) if minutos_trabalhados > 0 else None
        
        status_class = 'regular'
        if registro.status:
            if 'extra' in registro.status.lower():
                status_class = 'extra'
            elif 'irregular' in registro.status.lower():
                status_class = 'irregular'
        
        return {
            'id': registro.id,
            'data': registro.data.strftime("%d/%m/%Y"),
            'data_iso': registro.data.isoformat(),
            'dia_semana': self._get_dia_semana(registro.data.weekday()),
            'entrada': horario_entrada,
            'saida': horario_saida,
            'total': horas_trabalhadas,
            'minutos_trabalhados': minutos_trabalhados,
            'status': registro.get_status_display() if registro.status else 'Regular',
            'status_class': status_class
        }
    
    def _formatar_registro_detalhado(self, registro):
        dados = self._formatar_registro(registro)
        dados.update({
            'entrada_completa': registro.horario_entrada.strftime("%d/%m/%Y %H:%M") if registro.horario_entrada else None,
            'saida_completa': registro.horario_saida.strftime("%d/%m/%Y %H:%M") if registro.horario_saida else None,
            'observacao': registro.observacao,
            'criado_em': registro.criado_em.strftime("%d/%m/%Y %H:%M") if registro.criado_em else None,
            'atualizado_em': registro.atualizado_em.strftime("%d/%m/%Y %H:%M") if registro.atualizado_em else None,
        })
        return dados
    
    def _identificar_dias_sem_registro(self, ano, mes, registros):
        dias_com_registro = {r.data.day for r in registros}
        ultimo_dia = calendar.monthrange(ano, mes)[1]
        
        dias_sem_registro = []
        for dia in range(1, ultimo_dia + 1):
            if dia not in dias_com_registro:
                dias_sem_registro.append({
                    'dia': dia,
                    'data': f"{dia:02d}/{mes:02d}/{ano}",
                    'data_iso': f"{ano}-{mes:02d}-{dia:02d}"
                })
        
        return dias_sem_registro
    
    def _calcular_estatisticas(self, total_minutos, dias_com_registro, total_registros):
        if dias_com_registro == 0:
            return {
                'total_horas': '00:00',
                'media_diaria': '00:00',
                'total_minutos': 0
            }
        
        media_minutos = total_minutos // dias_com_registro
        
        return {
            'total_horas': self._formatar_minutos(total_minutos),
            'media_diaria': self._formatar_minutos(media_minutos),
            'total_minutos': total_minutos,
            'dias_media': dias_com_registro
        }
    
    def _calcular_dias_semana(self, registros):
        dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        distribuicao = {dia: 0 for dia in dias}
        
        for registro in registros:
            dia_idx = registro.data.weekday()
            distribuicao[dias[dia_idx]] += 1
        
        return distribuicao
    
    def _formatar_minutos(self, minutos):
        if not minutos:
            return "00:00"
        horas = minutos // 60
        mins = minutos % 60
        return f"{horas:02d}:{mins:02d}"
    
    def _get_nome_mes(self, mes):
        meses = [
            'Janeiro', 'Fevereiro', 'Março', 'Abril',
            'Maio', 'Junho', 'Julho', 'Agosto',
            'Setembro', 'Outubro', 'Novembro', 'Dezembro'
        ]
        return meses[mes - 1]
    
    def _get_dia_semana(self, dia_idx):
        dias = ['Segunda', 'Terça', 'Quarta', 'Quinta', 'Sexta', 'Sábado', 'Domingo']
        return dias[dia_idx]
    

class DashboardResumoAPIView(APIView):

    def get(self, request):
        hoje = timezone.now().date()
        
        total_usuarios = User.objects.count()
        registros_hoje = RegistroPonto.objects.filter(data=hoje).count()
        horas_extras = RegistroPonto.objects.filter(status='hora_extra').count()
        faltas = RegistroPonto.objects.filter(status='falta').count()
        
        status_counts = RegistroPonto.objects.values('status').annotate(
            quantidade=Count('id')
        )
        
        status_map = {
            'horario_regular': 'Horário Regular',
            'hora_extra': 'Hora Extra',
            'horario_irregular': 'Horário Irregular',
            'falta': 'Falta'
        }
        
        status_distribuicao = []
        for item in status_counts:
            status_distribuicao.append({
                'status': status_map.get(item['status'], item['status']),
                'quantidade': item['quantidade']
            })
        
        ultimos_7_dias = []
        labels_7_dias = []
        
        for i in range(6, -1, -1):
            data = hoje - timedelta(days=i)
            labels_7_dias.append(data.strftime('%d/%m'))
            count = RegistroPonto.objects.filter(data=data).count()
            ultimos_7_dias.append(count)
        
        horas_extras_7_dias = []
        faltas_7_dias = []
        
        for i in range(6, -1, -1):
            data = hoje - timedelta(days=i)
            horas_extras_7_dias.append(
                RegistroPonto.objects.filter(data=data, status='hora_extra').count()
            )
            faltas_7_dias.append(
                RegistroPonto.objects.filter(data=data, status='falta').count()
            )
        
        top_usuarios = RegistroPonto.objects.values(
            'usuario__name', 'usuario__email'
        ).annotate(
            total_registros=Count('id')
        ).order_by('-total_registros')[:5]
        
        top_usuarios_list = []
        for user in top_usuarios:
            top_usuarios_list.append({
                'nome': user['usuario__name'] or user['usuario__email'],
                'email': user['usuario__email'],
                'total': user['total_registros']
            })
        
        registros = RegistroPonto.objects.select_related('usuario').all().order_by('-data', '-horario_entrada')[:100]
        
        registros_lista = []
        for registro in registros:
            
            status_display = {
                'horario_regular': 'presente',
                'hora_extra': 'extra',
                'horario_irregular': 'atrasado',
                'falta': 'ausente'
            }.get(registro.status, 'presente')
            
            horas_trabalhadas = '0'
            if registro.horario_entrada and registro.horario_saida:
                horas_trabalhadas = '8'
            
            registros_lista.append({
                'usuario': registro.usuario.name or registro.usuario.email,
                'email': registro.usuario.email,
                'data': registro.data.isoformat(),
                'entrada': registro.horario_entrada.strftime('%H:%M') if registro.horario_entrada else '--:--',
                'saida': registro.horario_saida.strftime('%H:%M') if registro.horario_saida else '--:--',
                'horas_trabalhadas': horas_trabalhadas,
                'status': status_display.capitalize()
            })
        
        data = {
            "total_usuarios": total_usuarios,
            "registros_hoje": registros_hoje,
            "horas_extras": horas_extras,
            "faltas": faltas,
            
            "graficos": {
                "pizza": {
                    "labels": [item['status'] for item in status_distribuicao],
                    "dados": [item['quantidade'] for item in status_distribuicao]
                },
                "barras": {
                    "labels": labels_7_dias,
                    "dados": ultimos_7_dias
                },
                "linha": {
                    "labels": labels_7_dias,
                    "datasets": {
                        "horas_extras": horas_extras_7_dias,
                        "faltas": faltas_7_dias
                    }
                },
                "top_usuarios": top_usuarios_list
            },
            
            "registros_tabela": {
                "registros": registros_lista,
                "total": len(registros_lista)
            }
        }
        
        return Response(data)