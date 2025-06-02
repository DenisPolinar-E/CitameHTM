from django.db.models import Count, Q, Case, When, IntegerField, Sum, F, Value
from django.db.models.functions import TruncMonth, TruncWeek, TruncDay, Coalesce
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from django.http import JsonResponse
from datetime import datetime, timedelta

from .models import Cita, Especialidad, Medico, TratamientoProgramado, Derivacion, Usuario, Rol


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_origen_citas(request):
    """
    API para obtener estadísticas de citas según su origen: 
    - Citas creadas por paciente
    - Citas por derivación
    - Citas por seguimiento
    - Citas realizadas por admisión
    """
    try:
        # Obtener parámetros de filtro
        fecha_inicio_str = request.GET.get('fecha_inicio', None)
        fecha_fin_str = request.GET.get('fecha_fin', None)
        especialidad_id = request.GET.get('especialidad', None)
        medico_id = request.GET.get('medico', None)
    
        # Validar y convertir fechas
        try:
            if fecha_inicio_str:
                fecha_inicio = datetime.strptime(fecha_inicio_str, '%Y-%m-%d').date()
            else:
                fecha_inicio = (timezone.now().date() - timedelta(days=30))
                
            if fecha_fin_str:
                fecha_fin = datetime.strptime(fecha_fin_str, '%Y-%m-%d').date()
            else:
                fecha_fin = timezone.now().date()
        except ValueError:
            return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD.'}, status=400)
        
        # Base de consulta con filtro de fechas
        query_base = Cita.objects.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin
        )
        
        # Aplicar filtros adicionales si se proporcionan
        if especialidad_id:
            query_base = query_base.filter(medico__especialidad_id=especialidad_id)
        
        if medico_id:
            query_base = query_base.filter(medico_id=medico_id)
        
        # Obtener IDs de roles
        try:
            # Buscar rol de paciente (id 1 según la imagen)
            try:
                rol_paciente = Rol.objects.get(nombre__icontains='paciente').id
            except Rol.DoesNotExist:
                # Si no encuentra por nombre, intentar por ID
                rol_paciente = 1
                print(f"Usando ID fijo para rol_paciente: {rol_paciente}")
            
            # Buscar rol de admisión (id 3 según la imagen)
            try:
                # Intentar primero sin tilde
                rol_admision = Rol.objects.get(nombre__icontains='admision').id
            except Rol.DoesNotExist:
                try:
                    # Intentar con tilde por si acaso
                    rol_admision = Rol.objects.get(nombre__icontains='admisión').id
                except Rol.DoesNotExist:
                    # Si todo falla, usar el ID fijo
                    rol_admision = 3
                    print(f"Usando ID fijo para rol_admision: {rol_admision}")
            
            print(f"Roles encontrados - Paciente: {rol_paciente}, Admisión: {rol_admision}")
            
        except Exception as e:
            print(f"Error al obtener roles: {str(e)}")
            return Response({'error': 'No se encontraron los roles necesarios: ' + str(e)}, status=500)
        
        # 1. Citas creadas por paciente
        citas_por_paciente = query_base.filter(
            reservado_por__rol_id=rol_paciente
        ).count()
        
        # 2. Citas por derivación
        citas_por_derivacion = query_base.filter(
            derivacion__isnull=False
        ).count()
        
        # 3. Citas por seguimiento (tienen seguimiento_sesion, cita anterior o están asociadas a un tratamiento)
        citas_por_seguimiento = query_base.filter(
            Q(seguimiento_sesion__isnull=False) | 
            Q(cita_anterior__isnull=False) | 
            Q(tratamiento__isnull=False)
        ).count()
        
        # 4. Citas realizadas por admisión
        citas_por_admision = query_base.filter(
            reservado_por__rol_id=rol_admision
        ).count()
        
        # Calcular estadísticas por estado para cada origen
        estados = ['pendiente', 'confirmada', 'atendida', 'cancelada']
        
        # Estadísticas por estado para cada tipo de origen
        estados_paciente = {}
        estados_derivacion = {}
        estados_seguimiento = {}
        estados_admision = {}
    
        for estado in estados:
            estados_paciente[estado] = query_base.filter(
                reservado_por__rol_id=rol_paciente,
                estado=estado
            ).count()
            
            estados_derivacion[estado] = query_base.filter(
                derivacion__isnull=False,
                estado=estado
            ).count()
            
            estados_seguimiento[estado] = query_base.filter(
                Q(seguimiento_sesion__isnull=False) | 
                Q(cita_anterior__isnull=False) | 
                Q(tratamiento__isnull=False),
                estado=estado
            ).count()
            
            estados_admision[estado] = query_base.filter(
                reservado_por__rol_id=rol_admision,
                estado=estado
            ).count()
    
        # Distribución por día de la semana para cada origen
        dias_semana_paciente = {}
        dias_semana_derivacion = {}
        dias_semana_seguimiento = {}
        dias_semana_admision = {}
        
        # Consulta para pacientes
        dist_dia_paciente = query_base.filter(reservado_por__rol_id=rol_paciente).annotate(
            dia_semana=TruncDay('fecha')
        ).values('dia_semana').annotate(
            total=Count('id')
        ).order_by('dia_semana')
        
        for item in dist_dia_paciente:
            if item['dia_semana']:
                dias_semana_paciente[item['dia_semana'].strftime('%Y-%m-%d')] = item['total']
    
        # Consulta para derivaciones
        dist_dia_derivacion = query_base.filter(derivacion__isnull=False).annotate(
            dia_semana=TruncDay('fecha')
        ).values('dia_semana').annotate(
            total=Count('id')
        ).order_by('dia_semana')
        
        for item in dist_dia_derivacion:
            if item['dia_semana']:
                dias_semana_derivacion[item['dia_semana'].strftime('%Y-%m-%d')] = item['total']
    
        # Consulta para seguimientos
        dist_dia_seguimiento = query_base.filter(
            Q(seguimiento_sesion__isnull=False) | 
            Q(cita_anterior__isnull=False) | 
            Q(tratamiento__isnull=False)
        ).annotate(
            dia_semana=TruncDay('fecha')
        ).values('dia_semana').annotate(
            total=Count('id')
        ).order_by('dia_semana')
        
        for item in dist_dia_seguimiento:
            if item['dia_semana']:
                dias_semana_seguimiento[item['dia_semana'].strftime('%Y-%m-%d')] = item['total']
    
        # Consulta para admisión
        dist_dia_admision = query_base.filter(reservado_por__rol_id=rol_admision).annotate(
            dia_semana=TruncDay('fecha')
        ).values('dia_semana').annotate(
            total=Count('id')
        ).order_by('dia_semana')
        
        for item in dist_dia_admision:
            if item['dia_semana']:
                dias_semana_admision[item['dia_semana'].strftime('%Y-%m-%d')] = item['total']
    
        # Distribución por especialidad para cada origen
        especialidades_paciente = list(query_base.filter(reservado_por__rol_id=rol_paciente).values(
            'medico__especialidad__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total'))
        
        especialidades_derivacion = list(query_base.filter(derivacion__isnull=False).values(
            'medico__especialidad__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total'))
        
        especialidades_seguimiento = list(query_base.filter(
            Q(seguimiento_sesion__isnull=False) | 
            Q(cita_anterior__isnull=False) | 
            Q(tratamiento__isnull=False)
        ).values(
            'medico__especialidad__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total'))
        
        especialidades_admision = list(query_base.filter(reservado_por__rol_id=rol_admision).values(
            'medico__especialidad__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total'))
    
        # Preparar respuesta
        respuesta = {
            'total_general': query_base.count(),
            'distribucion_origen': {
                'paciente': citas_por_paciente,
                'derivacion': citas_por_derivacion,
                'seguimiento': citas_por_seguimiento,
                'admision': citas_por_admision
            },
            'estados': {
                'paciente': estados_paciente,
                'derivacion': estados_derivacion,
                'seguimiento': estados_seguimiento,
                'admision': estados_admision
            },
            'dias_semana': {
                'paciente': dias_semana_paciente,
                'derivacion': dias_semana_derivacion,
                'seguimiento': dias_semana_seguimiento,
                'admision': dias_semana_admision
            },
            'especialidades': {
                'paciente': especialidades_paciente,
                'derivacion': especialidades_derivacion,
                'seguimiento': especialidades_seguimiento,
                'admision': especialidades_admision
            }
        }
        
        return Response(respuesta)
    except Exception as e:
        import traceback
        print(f"Error en api_origen_citas: {str(e)}")
        print(traceback.format_exc())
        return Response({
            'error': str(e),
            'mensaje': 'Ocurrió un error al procesar la solicitud. Por favor, contacte al administrador.'
        }, status=500)
