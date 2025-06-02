from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Count, Q, F, Sum, Case, When, Value, IntegerField
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from datetime import datetime, timedelta
from .models import Cita, Medico, Especialidad, Paciente, Notificacion, Derivacion
import json

@login_required
def analisis_citas_admision(request):
    """
    Vista para mostrar análisis de citas registradas por admisión
    """
    # Verificar que el usuario tenga rol de administrador
    if not request.user.rol or request.user.rol.nombre != 'Administrador':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('dashboard_view')
    
    # Obtener todas las especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Configurar fechas predeterminadas (mes actual)
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    ultimo_dia_mes = (primer_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Información para el menú lateral y panel de administrador
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_citas = Cita.objects.count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    citas_atendidas = Cita.objects.filter(estado='atendida').count()
    
    citas_por_especialidad = Cita.objects.values('medico__especialidad__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leido=False
    ).order_by('-fecha_envio')[:5]
    
    # Contexto para la plantilla
    context = {
        'titulo': 'Análisis de Citas por Admisión',
        'especialidades': especialidades,
        'fecha_inicio': primer_dia_mes,
        'fecha_fin': ultimo_dia_mes,
        
        # Datos para el menú lateral y dashboard
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_atendidas': citas_atendidas,
        'citas_por_especialidad': citas_por_especialidad,
        'notificaciones': notificaciones,
    }
    
    return render(request, 'admin/analisis_citas_admision.html', context)

@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_citas_admision(request):
    """
    API para obtener datos de citas registradas por admisión
    """
    try:
        # Obtener parámetros de filtrado
        fecha_inicio = request.GET.get('fecha_inicio', '')
        fecha_fin = request.GET.get('fecha_fin', '')
        especialidad_id = request.GET.get('especialidad_id', '')
        medico_id = request.GET.get('medico_id', '')
        
        # Validar fechas
        if fecha_inicio and fecha_fin:
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                return Response({'error': 'Formato de fecha inválido. Use YYYY-MM-DD'}, status=400)
        else:
            # Fechas predeterminadas: mes actual
            hoy = timezone.now().date()
            fecha_inicio = hoy.replace(day=1)
            fecha_fin = (fecha_inicio + timedelta(days=32)).replace(day=1) - timedelta(days=1)
        
        # Base de la consulta: citas registradas por admisión
        # Asumimos que las citas de admisión son las que tienen reservado_por='personal' o tienen un campo específico
        query = Cita.objects.filter(
            fecha__gte=fecha_inicio,
            fecha__lte=fecha_fin,
            # Agregar condición para identificar citas de admisión
            # Por ejemplo: reservado_por='personal' o tipo_origen='admision'
            # Esto dependerá de la estructura actual de la base de datos
        )
        
        # Aplicar filtros adicionales
        if especialidad_id and especialidad_id.isdigit():
            query = query.filter(medico__especialidad_id=especialidad_id)
        
        if medico_id and medico_id.isdigit():
            query = query.filter(medico_id=medico_id)
        
        # Estadísticas generales
        total_citas = query.count()
        citas_atendidas = query.filter(estado='atendida').count()
        citas_pendientes = query.filter(estado='pendiente').count()
        citas_canceladas = query.filter(estado='cancelada').count()
        
        # Distribución por especialidad
        por_especialidad = query.values(
            'medico__especialidad__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total')
        
        # Distribución por médico (top 10)
        por_medico = query.values(
            'medico__usuario__nombres',
            'medico__usuario__apellidos',
            'medico__especialidad__nombre'
        ).annotate(
            total=Count('id')
        ).order_by('-total')[:10]
        
        # Distribución por día de la semana
        por_dia_semana = query.annotate(
            dia_semana=F('fecha__week_day')
        ).values('dia_semana').annotate(
            total=Count('id')
        ).order_by('dia_semana')
        
        # Convertir días de la semana a nombres
        dias_semana = ['Lunes', 'Martes', 'Miércoles', 'Jueves', 'Viernes', 'Sábado', 'Domingo']
        por_dia_semana_formateado = []
        for item in por_dia_semana:
            # Django usa 1-7 para días de la semana, donde 1 es domingo y 7 es sábado
            # Convertimos a formato 0-6 donde 0 es lunes y 6 es domingo
            dia_indice = (item['dia_semana'] - 2) % 7
            por_dia_semana_formateado.append({
                'dia': dias_semana[dia_indice],
                'total': item['total']
            })
        
        # Preparar respuesta
        respuesta = {
            'total_citas': total_citas,
            'citas_atendidas': citas_atendidas,
            'citas_pendientes': citas_pendientes,
            'citas_canceladas': citas_canceladas,
            'por_especialidad': list(por_especialidad),
            'por_medico': [{
                'nombre': f"{item['medico__usuario__nombres']} {item['medico__usuario__apellidos']}",
                'especialidad': item['medico__especialidad__nombre'],
                'total': item['total']
            } for item in por_medico],
            'por_dia_semana': por_dia_semana_formateado
        }
        
        return Response(respuesta)
    
    except Exception as e:
        import traceback
        return Response({
            'error': str(e),
            'traceback': traceback.format_exc()
        }, status=500)
