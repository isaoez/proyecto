# myapp/context_processors.py
from .models import Oferta, TruequeSugerido

def notificaciones_pendientes(request):
    if not request.user.is_authenticated:
        return {}

    # 1. Contar ofertas 1-a-1 recibidas y pendientes
    try:
        ofertas_count = Oferta.objects.filter(
            articulo_deseado__propietario=request.user, 
            estado='PENDIENTE'
        ).count()
    except:
        ofertas_count = 0

    # 2. Contar trueques de cadena sugeridos
    try:
        trueques_count = TruequeSugerido.objects.filter(
            participantes=request.user, 
            estado='SUGERIDO'
        ).exclude(
            # Excluimos los que ya aceptamos para no notificar de nuevo
            usuarios_que_aceptaron=request.user
        ).count()
    except:
        trueques_count = 0

    # 3. Devolvemos el diccionario
    return {
        'ofertas_pendientes_count': ofertas_count,
        'trueques_pendientes_count': trueques_count,
    }