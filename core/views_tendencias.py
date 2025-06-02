"""
Vistas para el análisis de tendencias de citas médicas
"""

from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.http import JsonResponse
from django.db.models import Min, Max, Count, Q
from datetime import datetime, timedelta
import logging
from .models import Cita, Especialidad, Medico, Paciente, Notificacion

# Configurar logger
logger = logging.getLogger(__name__)

def es_administrador(user):
    """Verifica si un usuario tiene rol de administrador"""
    if not user.rol:
        return False
    return user.rol.nombre.lower() in ['admin', 'administrador']

def es_recepcionista(user):
    """Verifica si un usuario tiene rol de recepcionista/admisión"""
    if not user.rol:
        return False
    return user.rol.nombre.lower() in ['admision', 'recepcion', 'recepcionista']

@login_required
def tendencias_citas(request):
    """
    Vista para la página de análisis de tendencias de citas
    """
    # Verificar permisos del usuario
    if not es_recepcionista(request.user) and not es_administrador(request.user):
        return redirect('inicio')
        
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
    
    # Obtener lista de especialidades para el filtro de tendencias
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    context = {
        # Datos para el filtro de tendencias
        'especialidades': especialidades,
        
        # Datos para el menú lateral y dashboard
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_atendidas': citas_atendidas,
        'citas_por_especialidad': citas_por_especialidad,
        'notificaciones': notificaciones,
    }
    
    return render(request, 'admin/tendencias_citas.html', context)

@login_required
def api_tendencias_citas(request):
    """
    API que devuelve datos para el gráfico de tendencias
    """
    try:
        # Verificar permisos del usuario
        if not es_recepcionista(request.user) and not es_administrador(request.user):
            return JsonResponse({'error': 'No tiene permisos para ver esta información'}, status=403)
            
        # Obtener parámetros
        fecha_inicio = request.GET.get('fecha_inicio')
        fecha_fin = request.GET.get('fecha_fin')
        especialidad_id = request.GET.get('especialidad_id')
        medico_id = request.GET.get('medico_id')
        agrupacion = request.GET.get('agrupacion', 'dia')
        estados_param = request.GET.get('estados', '')
        
        # Lista de estados válidos en el sistema (siempre en minúsculas)
        ESTADOS_VALIDOS = ['pendiente', 'confirmada', 'atendida', 'cancelada']
        
        # Lista de estados a incluir (normalizados a minúsculas)
        if estados_param:
            estados_incluir = [estado.lower() for estado in estados_param.split(',') if estado.lower() in ESTADOS_VALIDOS]
        else:
            estados_incluir = ESTADOS_VALIDOS.copy()
        
        # Validar fechas
        try:
            fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
            fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
        except (ValueError, TypeError):
            return JsonResponse({'error': 'Formato de fecha inválido'}, status=400)
        
        # Query base para citas en el período
        query = Cita.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
        
        # Aplicar filtros adicionales
        if especialidad_id and especialidad_id != '0':
            query = query.filter(medico__especialidad__id=especialidad_id)
            
        if medico_id and medico_id != '0' and medico_id.isdigit():
            query = query.filter(medico__id=medico_id)
            
        # Ordenar por fecha
        query = query.order_by('fecha')
        
        # Definir función de agrupación según parámetro
        def agrupar_por_dia(fecha):
            return fecha.strftime('%Y-%m-%d')
            
        def agrupar_por_semana(fecha):
            # Formato: 2023-W01 (año-semana)
            return fecha.strftime('%G-W%V')
            
        def agrupar_por_mes(fecha):
            return fecha.strftime('%Y-%m')
        
        # Seleccionar función de agrupación
        if agrupacion == 'semana':
            func_agrupacion = agrupar_por_semana
        elif agrupacion == 'mes':
            func_agrupacion = agrupar_por_mes
        else:  # default: dia
            func_agrupacion = agrupar_por_dia
        
        # Diccionarios para almacenar datos
        fechas_unicas = set()
        valores_por_estado = {
            'pendiente': {},
            'confirmada': {},
            'atendida': {},
            'cancelada': {}
        }
        
        # Contadores globales para métricas
        total_citas = 0
        total_atendidas = 0
        total_canceladas = 0
        
        # Procesar citas
        for cita in query:
            grupo_fecha = func_agrupacion(cita.fecha)
            fechas_unicas.add(grupo_fecha)
            
            # Asegurarnos de que el estado esté en minúsculas
            estado = cita.estado.lower()
            
            # Contar por estado
            if estado in valores_por_estado:
                if grupo_fecha not in valores_por_estado[estado]:
                    valores_por_estado[estado][grupo_fecha] = 0
                valores_por_estado[estado][grupo_fecha] += 1
            
            # Actualizar contadores globales
            total_citas += 1
            if estado == 'atendida':
                total_atendidas += 1
            elif estado == 'cancelada':
                total_canceladas += 1
        
        # Convertir fechas a lista ordenada
        fechas_lista = sorted(list(fechas_unicas))
        
        # Completar valores faltantes con ceros
        for estado in valores_por_estado:
            if estado in estados_incluir:
                for fecha in fechas_lista:
                    if fecha not in valores_por_estado[estado]:
                        valores_por_estado[estado][fecha] = 0
        
        # Convertir a listas ordenadas para el gráfico
        valores_listas = {}
        for estado in estados_incluir:
            if estado in valores_por_estado:
                valores_listas[estado] = [valores_por_estado[estado].get(fecha, 0) for fecha in fechas_lista]
        
        # Calcular métricas
        metricas = {
            'total_citas': total_citas,
            'tasa_atencion': round((total_atendidas / total_citas * 100) if total_citas > 0 else 0, 1),
            'tasa_cancelacion': round((total_canceladas / total_citas * 100) if total_citas > 0 else 0, 1),
            'tendencia_mensual': calcular_tendencia_mensual(query)
        }
        
        # Verificar que hay datos para al menos un estado
        if not fechas_lista:
            logger.warning("No se encontraron datos para los filtros seleccionados")
            return JsonResponse({
                'fechas': [],
                'valores_por_estado': {},
                'agrupacion': agrupacion,
                'metricas': {
                    'total_citas': 0,
                    'tasa_atencion': 0,
                    'tasa_cancelacion': 0,
                    'tendencia_mensual': 0
                },
                'mensaje': 'No se encontraron datos para los filtros seleccionados'
            })
        
        # Preparar respuesta
        respuesta = {
            'fechas': fechas_lista,
            'valores_por_estado': valores_listas,
            'agrupacion': agrupacion,
            'metricas': metricas
        }
        
        # Registrar en el log la respuesta exitosa
        logger.info(f"API tendencias-citas devolvió datos con {len(fechas_lista)} puntos de tiempo y {len(valores_listas)} estados")
        
        return JsonResponse(respuesta)
        
    except Exception as e:
        logger.error(f"Error en api_tendencias_citas: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def api_medicos_por_especialidad_tendencias(request):
    """
    API que devuelve médicos filtrados por especialidad para el módulo de tendencias
    """
    try:
        especialidad_id = request.GET.get('especialidad_id')
        
        if not especialidad_id or especialidad_id == '0':
            medicos = Medico.objects.all().order_by('usuario__nombres')
        else:
            medicos = Medico.objects.filter(especialidad__id=especialidad_id).order_by('usuario__nombres')
            
        medicos_data = []
        for medico in medicos:
            nombre_completo = f"{medico.usuario.nombres} {medico.usuario.apellidos}"
            medicos_data.append({
                'id': medico.id,
                'nombre': nombre_completo
            })
        
        return JsonResponse({'medicos': medicos_data})
        
    except Exception as e:
        logger.error(f"Error en api_medicos_por_especialidad_tendencias: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

def calcular_tendencia_mensual(query):
    """
    Calcula la tendencia mensual de citas (porcentaje de variación)
    """
    try:
        # Si no hay suficientes datos, retornar 0
        if not query.exists():
            return 0
            
        # Obtener fecha más antigua y más reciente
        fecha_min = query.aggregate(Min('fecha'))['fecha__min']
        fecha_max = query.aggregate(Max('fecha'))['fecha__max']
        
        if not fecha_min or not fecha_max:
            return 0
            
        # Si el rango es menor a 30 días, no hay suficientes datos
        if (fecha_max - fecha_min).days < 30:
            return 0
            
        # Definir el mes actual y anterior
        mes_actual = fecha_max.replace(day=1)
        mes_anterior = (mes_actual - timedelta(days=1)).replace(day=1)
        
        # Contar citas en cada mes
        citas_mes_actual = query.filter(fecha__gte=mes_actual).count()
        citas_mes_anterior = query.filter(fecha__gte=mes_anterior, fecha__lt=mes_actual).count()
        
        # Calcular variación porcentual
        if citas_mes_anterior > 0:
            tendencia = ((citas_mes_actual - citas_mes_anterior) / citas_mes_anterior) * 100
            return round(tendencia, 1)
        else:
            return 100  # Si no había citas antes, es un crecimiento del 100%
            
    except Exception as e:
        logger.error(f"Error calculando tendencia mensual: {str(e)}")
        return 0
