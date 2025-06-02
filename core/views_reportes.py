from django.shortcuts import render, redirect, get_object_or_404
from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.utils import timezone
from datetime import datetime, timedelta
from .models import Cita, Especialidad, Medico
from .constants import ESTADO_CITA_PROGRAMADA, ESTADO_CITA_ATENDIDA, ESTADO_CITA_CANCELADA, ESTADO_CITA_INASISTENCIA

# Función original de distribución de citas
@login_required
def distribucion_citas(request):
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Distribución de Citas',
        'subtitulo': 'Análisis Temporal'
    }
    
    return render(request, 'admin/distribucion_citas.html', context)

# API para obtener datos de distribución de citas
@login_required
def api_distribucion_citas(request):
    periodo = request.GET.get('periodo', 'mensual')
    fecha_inicio = datetime.strptime(request.GET.get('fecha_inicio', ''), '%Y-%m-%d').date()
    fecha_fin = datetime.strptime(request.GET.get('fecha_fin', ''), '%Y-%m-%d').date()
    especialidad_id = request.GET.get('especialidad', '')
    medico_id = request.GET.get('medico', '')
    
    # Filtrar citas por fecha
    citas = Cita.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
    
    # Aplicar filtros adicionales si se proporcionan
    if especialidad_id:
        citas = citas.filter(medico__especialidad_id=especialidad_id)
    
    if medico_id:
        citas = citas.filter(medico_id=medico_id)
    
    # Contar citas por estado (usando los estados reales de la base de datos)
    total_citas = citas.count()
    citas_pendientes = citas.filter(estado='pendiente').count()
    citas_confirmadas = citas.filter(estado='confirmada').count()
    citas_atendidas = citas.filter(estado='atendida').count()
    citas_canceladas = citas.filter(estado='cancelada').count()
    
    # Calcular inasistencias (citas pasadas con asistio=False)
    fecha_actual = timezone.now().date()
    citas_inasistencia = citas.filter(
        fecha__lt=fecha_actual,
        asistio=False
    ).exclude(estado='cancelada').count()
    
    # Preparar datos para el gráfico
    labels = ['Pendientes', 'Confirmadas', 'Atendidas', 'Canceladas', 'Inasistencias']
    data = [citas_pendientes, citas_confirmadas, citas_atendidas, citas_canceladas, citas_inasistencia]
    
    # Colores para el gráfico
    colors = [
        'rgba(54, 162, 235, 0.7)',  # Azul para pendientes
        'rgba(255, 206, 86, 0.7)',  # Amarillo para confirmadas
        'rgba(75, 192, 192, 0.7)',  # Verde para atendidas
        'rgba(255, 99, 132, 0.7)',  # Rojo para canceladas
        'rgba(153, 102, 255, 0.7)',  # Morado para inasistencias
    ]
    
    # Preparar respuesta
    response = {
        'labels': labels,
        'datasets': [{
            'data': data,
            'backgroundColor': colors,
            'borderColor': colors,
            'borderWidth': 1
        }],
        'totales': {
            'total': total_citas,
            'pendientes': citas_pendientes,
            'confirmadas': citas_confirmadas,
            'atendidas': citas_atendidas,
            'canceladas': citas_canceladas,
            'inasistencias': citas_inasistencia
        }
    }
    
    return JsonResponse(response)


# API para obtener médicos por especialidad
@login_required
def api_medicos_por_especialidad(request):
    """
    API para obtener la lista de médicos filtrados por especialidad.
    Recibe el ID de especialidad como parámetro y devuelve un JSON con los médicos.
    """
    especialidad_id = request.GET.get('especialidad_id', '')
    
    # Si no se proporciona especialidad, devolver todos los médicos
    if not especialidad_id:
        medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    else:
        medicos = Medico.objects.filter(especialidad_id=especialidad_id).select_related('usuario', 'especialidad')
    
    # Formatear la respuesta
    medicos_data = []
    for medico in medicos:
        medicos_data.append({
            'id': medico.id,
            'nombre': f"{medico.usuario.nombres} {medico.usuario.apellidos}",
            'especialidad': medico.especialidad.nombre
        })
    
    return JsonResponse({'medicos': medicos_data})

# ---- Funciones adicionales para Análisis Temporal ----
@login_required
def comparativas(request):
    """
    Vista para mostrar comparativas de citas entre diferentes períodos.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Comparativas de Citas',
        'subtitulo': 'Análisis Temporal'
    }
    
    return render(request, 'admin/comparativas_citas.html', context)


@login_required
def tendencias(request):
    """
    Vista para mostrar tendencias en la programación de citas a lo largo del tiempo.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Tendencias de Citas',
        'subtitulo': 'Análisis Temporal'
    }
    
    return render(request, 'admin/tendencias.html', context)


@login_required
def tasas_asistencia(request):
    """
    Vista para mostrar las tasas de asistencia a citas programadas.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Tasas de Asistencia',
        'subtitulo': 'Análisis Temporal'
    }
    
    return render(request, 'admin/tasas_asistencia.html', context)


# ---- Funciones para Análisis por Origen ----
@login_required
def citas_admision(request):
    """
    Vista para mostrar análisis de citas creadas por admisión.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas por Admisión',
        'subtitulo': 'Análisis por Origen'
    }
    
    # Incluye la ruta completa y la plantilla exacta que estamos tratando de renderizar
    template_name = 'admin/citas_admision.html'
    print(f"Intentando renderizar la plantilla: {template_name}")
    return render(request, template_name, context)

@login_required
def origen_citas(request):
    """
    Vista para mostrar análisis de citas según su origen: paciente, derivación, seguimiento y admisión.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    # Determinar el título según la URL
    current_url = request.path
    
    if 'derivacion' in current_url:
        titulo = 'Análisis por Derivación'
        subtitulo = 'Distribución y estadísticas de citas por origen'
    else:
        titulo = 'Análisis por Origen de Citas'
        subtitulo = 'Clasificación según origen: Paciente, Derivación, Seguimiento y Admisión'
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': titulo,
        'subtitulo': subtitulo
    }
    
    # Siempre usar la misma plantilla, independientemente de la URL
    return render(request, 'admin/origen_citas.html', context)


@login_required
def citas_derivacion(request):
    """
    Vista para mostrar análisis de citas creadas por derivación médica.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas por Derivación',
        'subtitulo': 'Análisis por Origen'
    }
    
    return render(request, 'admin/citas_derivacion.html', context)


@login_required
def citas_seguimiento(request):
    """
    Vista para mostrar análisis de citas creadas para seguimiento de tratamientos.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas de Seguimiento',
        'subtitulo': 'Análisis por Origen'
    }
    
    return render(request, 'admin/citas_seguimiento.html', context)


# ---- Funciones para Análisis por Especialidad y Médico ----
@login_required
def analisis_especialidad(request):
    """
    Vista para mostrar análisis de citas por especialidad médica.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Análisis por Especialidad',
        'subtitulo': 'Distribución de Citas'
    }
    
    return render(request, 'admin/analisis_especialidad.html', context)


@login_required
def analisis_medico(request):
    """
    Vista para mostrar análisis de citas por médico.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Análisis por Médico',
        'subtitulo': 'Distribución de Citas'
    }
    
    return render(request, 'admin/analisis_medico.html', context)


# ---- Funciones para Análisis de Estado ----
@login_required
def citas_completadas(request):
    """
    Vista para mostrar análisis de citas completadas (atendidas).
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas Completadas',
        'subtitulo': 'Análisis de Estado'
    }
    
    return render(request, 'admin/citas_completadas.html', context)


@login_required
def citas_canceladas(request):
    """
    Vista para mostrar análisis de citas canceladas.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas Canceladas',
        'subtitulo': 'Análisis de Estado'
    }
    
    return render(request, 'admin/citas_canceladas.html', context)


@login_required
def citas_inasistencias(request):
    """
    Vista para mostrar análisis de inasistencias a citas.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Inasistencias',
        'subtitulo': 'Análisis de Estado'
    }
    
    return render(request, 'admin/citas_inasistencias.html', context)


# ---- Funciones para Reportes Especiales ----
@login_required
def reporte_pacientes(request):
    """
    Vista para mostrar reportes especiales sobre pacientes (frecuentes y nuevos).
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Reporte de Pacientes',
        'subtitulo': 'Reportes Especiales'
    }
    
    return render(request, 'admin/reporte_pacientes.html', context)


@login_required
def reporte_satisfaccion(request):
    """
    Vista para mostrar reportes de satisfacción de pacientes.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Satisfacción de Pacientes',
        'subtitulo': 'Reportes Especiales'
    }
    
    return render(request, 'admin/reporte_satisfaccion.html', context)


@login_required
def indicadores_clave(request):
    """
    Vista para mostrar indicadores clave de rendimiento del hospital.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Indicadores Clave',
        'subtitulo': 'Reportes Especiales'
    }
    
    return render(request, 'admin/indicadores_clave.html', context)
