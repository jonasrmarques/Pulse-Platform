from datetime import datetime, time, timedelta

def calcular_horas_trabalhadas(horario_entrada, horario_saida):
    """
    Calcula a diferença entre dois horários e retorna no formato HH:MM
    """
    if not horario_entrada or not horario_saida:
        return None
    
    # Converte time para datetime do dia atual para calcular diferença
    hoje = datetime.now().date()
    
    entrada = datetime.combine(hoje, horario_entrada)
    saida = datetime.combine(hoje, horario_saida)
    
    # Se a saída for menor que a entrada, assume que passou da meia-noite
    if saida < entrada:
        saida = saida + timedelta(days=1)
    
    diferenca = saida - entrada
    
    # Formata como HH:MM
    horas = diferenca.seconds // 3600
    minutos = (diferenca.seconds % 3600) // 60
    
    return f"{horas:02d}:{minutos:02d}"