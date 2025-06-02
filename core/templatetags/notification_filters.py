from django import template
from django.db.models import Q
from core.models import Cita
from django.utils import timezone
import logging

logger = logging.getLogger(__name__)
register = template.Library()

@register.filter
def filter_notificaciones_activas(notificaciones):
    """
    Filtra las notificaciones para excluir aquellas relacionadas con citas ya atendidas
    y ordena las notificaciones con las no leídas primero
    
    Args:
        notificaciones: Queryset de notificaciones
        
    Returns:
        Queryset filtrado de notificaciones
    """
    # Crear una lista para almacenar los IDs de notificaciones a excluir
    ids_a_excluir = []
    
    # Revisar cada notificación
    for notificacion in notificaciones:
        try:
            # Si la notificación está relacionada con una cita
            if notificacion.objeto_relacionado == 'cita' and notificacion.objeto_id:
                try:
                    # Intentar obtener la cita
                    cita = Cita.objects.get(id=notificacion.objeto_id)
                    # Si la cita ya fue atendida, agregar la notificación a la lista de exclusión
                    if cita.estado == 'atendida':
                        ids_a_excluir.append(notificacion.id)
                        # Registrar para depuración
                        logger.debug(f"Excluyendo notificación ID {notificacion.id} - Cita atendida ID {cita.id}")
                except Cita.DoesNotExist:
                    # Si la cita no existe, también excluir la notificación
                    ids_a_excluir.append(notificacion.id)
                    logger.debug(f"Excluyendo notificación ID {notificacion.id} - Cita no existe")
        except Exception as e:
            # Capturar cualquier error y continuar con la siguiente notificación
            logger.error(f"Error al procesar notificación: {str(e)}")
            continue
    
    # Filtrar el queryset original para excluir las notificaciones identificadas
    notificaciones_filtradas = notificaciones.exclude(id__in=ids_a_excluir)
    
    # Ordenar las notificaciones con las no leídas primero y luego por fecha de envío (más recientes primero)
    notificaciones_ordenadas = sorted(
        notificaciones_filtradas,
        key=lambda n: (n.leido, -int(n.fecha_envio.timestamp()))
    )
    
    # Para depuración
    logger.debug(f"Total notificaciones: {notificaciones.count()}, Excluidas: {len(ids_a_excluir)}, Restantes: {len(notificaciones_ordenadas)}")
    
    return notificaciones_ordenadas

@register.filter
def get_notification_icon(tipo):
    """
    Retorna el icono de Font Awesome según el tipo de notificación
    """
    iconos = {
        'confirmacion': 'check-circle',
        'recordatorio': 'clock',
        'cancelacion': 'times-circle',
        'advertencia': 'exclamation-triangle',
        'informacion': 'info-circle'
    }
    return iconos.get(tipo, 'bell')
