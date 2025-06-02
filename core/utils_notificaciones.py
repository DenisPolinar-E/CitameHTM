from django.urls import reverse

def generar_url_redireccion(tipo_objeto, objeto_id):
    """
    Genera la URL de redirección para una notificación según el tipo de objeto relacionado
    
    Args:
        tipo_objeto (str): Tipo de objeto ('cita', 'derivacion', etc.)
        objeto_id (int): ID del objeto
        
    Returns:
        str: URL de redirección o None si no aplica
    """
    if tipo_objeto == 'cita':
        return reverse('atender_paciente', kwargs={'cita_id': objeto_id})
    elif tipo_objeto == 'derivacion':
        return reverse('ver_derivacion', kwargs={'derivacion_id': objeto_id})
    elif tipo_objeto == 'historial':
        # Usamos la URL historial_medico en lugar de ver_historial_medico
        return reverse('historial_medico') + f'?paciente_id={objeto_id}'
    else:
        return None

def crear_notificacion(usuario, mensaje, tipo, importante=False, objeto_relacionado=None, objeto_id=None, creador=None):
    """
    Crea una notificación con URL de redirección si corresponde
    
    Args:
        usuario: Usuario destinatario de la notificación
        mensaje (str): Mensaje de la notificación
        tipo (str): Tipo de notificación (confirmacion, recordatorio, etc.)
        importante (bool): Si la notificación es importante
        objeto_relacionado (str): Tipo de objeto relacionado ('cita', 'derivacion', etc.)
        objeto_id (int): ID del objeto relacionado
        creador: Usuario que creó el objeto relacionado (para evitar notificaciones a uno mismo)
        
    Returns:
        Notificacion: Objeto de notificación creado o None si no se debe crear
    """
    from .models import Notificacion
    
    # Si el usuario es el mismo que creó el objeto, no crear notificación
    if creador and usuario.id == creador.id:
        return None
    
    url_redireccion = None
    if objeto_relacionado and objeto_id:
        url_redireccion = generar_url_redireccion(objeto_relacionado, objeto_id)
    
    return Notificacion.objects.create(
        usuario=usuario,
        mensaje=mensaje,
        tipo=tipo,
        importante=importante,
        objeto_relacionado=objeto_relacionado,
        objeto_id=objeto_id,
        url_redireccion=url_redireccion
    )
