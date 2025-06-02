from django.http import JsonResponse
from django.utils import timezone
from django.shortcuts import get_object_or_404
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from .models import Notificacion

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_notificaciones_leidas(request):
    """
    Marca todas las notificaciones no leídas del usuario como leídas,
    excluyendo las relacionadas con citas ya atendidas
    """
    try:
        from .models import Cita
        
        # Obtener todas las notificaciones no leídas
        notificaciones = request.user.notificaciones.filter(leido=False)
        
        # Filtrar las notificaciones relacionadas con citas atendidas
        ids_a_excluir = []
        for notificacion in notificaciones:
            if notificacion.objeto_relacionado == 'cita' and notificacion.objeto_id:
                try:
                    cita = Cita.objects.get(id=notificacion.objeto_id)
                    if cita.estado == 'atendida':
                        ids_a_excluir.append(notificacion.id)
                except Cita.DoesNotExist:
                    ids_a_excluir.append(notificacion.id)
        
        # Excluir las notificaciones identificadas
        notificaciones_filtradas = notificaciones.exclude(id__in=ids_a_excluir)
        count = notificaciones_filtradas.count()
        
        # Marcar como leídas solo las notificaciones válidas
        for notificacion in notificaciones_filtradas:
            notificacion.leido = True
            notificacion.fecha_lectura = timezone.now()
            notificacion.save()
        
        # Eliminar las notificaciones de citas atendidas
        notificaciones.filter(id__in=ids_a_excluir).delete()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificaciones marcadas como leídas',
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_notificacion_leida(request, notificacion_id):
    """
    Marca una notificación específica como leída
    """
    try:
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
        notificacion.leido = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        
        return JsonResponse({
            'success': True,
            'message': 'Notificación marcada como leída'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def eliminar_notificacion(request, notificacion_id):
    """
    Elimina una notificación específica por su ID
    """
    try:
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
        notificacion.delete()
        
        return JsonResponse({
            'success': True,
            'message': f'Notificación ID {notificacion_id} eliminada correctamente'
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e)
        }, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def limpiar_notificaciones_citas_atendidas(request):
    """
    Esta función ha sido desactivada temporalmente para evitar solicitudes constantes.
    Originalmente eliminaba todas las notificaciones relacionadas con citas atendidas.
    """
    # Devolver una respuesta vacía sin realizar ninguna acción
    return JsonResponse({
        'success': True,
        'message': 'Función desactivada temporalmente',
        'eliminadas': 0
    })

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def notificaciones_no_leidas_count(request):
    """
    Retorna el número de notificaciones no leídas del usuario,
    excluyendo las relacionadas con citas ya atendidas
    """
    try:
        from .models import Cita
        
        # Obtener todas las notificaciones no leídas
        notificaciones = request.user.notificaciones.filter(leido=False)
        
        # Filtrar las notificaciones relacionadas con citas atendidas
        ids_a_excluir = []
        for notificacion in notificaciones:
            if notificacion.objeto_relacionado == 'cita' and notificacion.objeto_id:
                try:
                    cita = Cita.objects.get(id=notificacion.objeto_id)
                    if cita.estado == 'atendida':
                        ids_a_excluir.append(notificacion.id)
                except Cita.DoesNotExist:
                    ids_a_excluir.append(notificacion.id)
        
        # Excluir las notificaciones identificadas
        notificaciones_filtradas = notificaciones.exclude(id__in=ids_a_excluir)
        count = notificaciones_filtradas.count()
        
        return JsonResponse({
            'success': True,
            'count': count
        })
    except Exception as e:
        return JsonResponse({
            'success': False,
            'message': str(e),
            'count': 0
        }, status=500)
