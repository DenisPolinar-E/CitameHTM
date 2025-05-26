from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta, time

from .models import Medico, DisponibilidadMedica, DIAS_SEMANA_CHOICES, TIPO_TURNO_CHOICES
from .forms import DisponibilidadMedicaForm

@login_required
def dashboard_medico(request):
    """Vista para el dashboard del médico"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        medico = request.user.medico
        
        # Obtener citas pendientes para hoy
        hoy = timezone.now().date()
        citas_hoy = medico.citas.filter(
            fecha=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('hora_inicio')
        
        # Obtener próximas citas (excluyendo las de hoy)
        proximas_citas = medico.citas.filter(
            fecha__gt=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora_inicio')[:5]
        
        # Obtener estadísticas
        total_citas = medico.citas.count()
        citas_pendientes = medico.citas.filter(estado='pendiente').count()
        citas_atendidas = medico.citas.filter(estado='atendida').count()
        
        # Obtener disponibilidades activas
        disponibilidades = medico.disponibilidades.filter(activo=True).order_by('dia_semana', 'hora_inicio')
        
        context = {
            'medico': medico,
            'citas_hoy': citas_hoy,
            'proximas_citas': proximas_citas,
            'total_citas': total_citas,
            'citas_pendientes': citas_pendientes,
            'citas_atendidas': citas_atendidas,
            'disponibilidades': disponibilidades,
        }
        
        return render(request, 'dashboard/medico/dashboard.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar el dashboard: {str(e)}')
        return redirect('home')

@login_required
def disponibilidad_medica(request):
    """Vista para gestionar la disponibilidad del médico"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        medico = request.user.medico
        
        # Obtener disponibilidades regulares (por día de semana)
        disponibilidades_regulares = medico.disponibilidades.filter(
            fecha_especial__isnull=True,
            activo=True
        ).order_by('dia_semana', 'hora_inicio')
        
        # Obtener disponibilidades especiales (fechas específicas)
        disponibilidades_especiales = medico.disponibilidades.filter(
            fecha_especial__isnull=False,
            activo=True
        ).order_by('fecha_especial', 'hora_inicio')
        
        # Obtener disponibilidades inactivas
        disponibilidades_inactivas = medico.disponibilidades.filter(
            activo=False
        ).order_by('-id')[:10]  # Mostrar solo las 10 más recientes
        
        # Preparar formulario para nueva disponibilidad
        form = DisponibilidadMedicaForm(initial={'medico': medico})
        
        if request.method == 'POST':
            form = DisponibilidadMedicaForm(request.POST)
            if form.is_valid():
                disponibilidad = form.save(commit=False)
                disponibilidad.medico = medico
                
                # Validar que no haya solapamiento con otras disponibilidades
                if disponibilidad.fecha_especial:
                    # Validar solapamiento para fecha específica
                    solapamiento = medico.disponibilidades.filter(
                        fecha_especial=disponibilidad.fecha_especial,
                        activo=True
                    ).filter(
                        Q(hora_inicio__lt=disponibilidad.hora_fin) & 
                        Q(hora_fin__gt=disponibilidad.hora_inicio)
                    ).exists()
                else:
                    # Validar solapamiento para día de semana
                    solapamiento = medico.disponibilidades.filter(
                        dia_semana=disponibilidad.dia_semana,
                        fecha_especial__isnull=True,
                        activo=True
                    ).filter(
                        Q(hora_inicio__lt=disponibilidad.hora_fin) & 
                        Q(hora_fin__gt=disponibilidad.hora_inicio)
                    ).exists()
                
                if solapamiento:
                    messages.error(request, 'El horario ingresado se solapa con otro horario existente.')
                else:
                    disponibilidad.save()
                    messages.success(request, 'Horario de disponibilidad guardado correctamente.')
                    return redirect('disponibilidad_medica')
        
        context = {
            'medico': medico,
            'disponibilidades_regulares': disponibilidades_regulares,
            'disponibilidades_especiales': disponibilidades_especiales,
            'disponibilidades_inactivas': disponibilidades_inactivas,
            'form': form,
            'dias_semana': DIAS_SEMANA_CHOICES,
            'tipos_turno': TIPO_TURNO_CHOICES,
        }
        
        return render(request, 'medico/disponibilidad.html', context)
    except Exception as e:
        messages.error(request, f'Error al cargar la página de disponibilidad: {str(e)}')
        return redirect('dashboard_medico')

@login_required
def editar_disponibilidad(request, disponibilidad_id):
    """Vista para editar una disponibilidad existente"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        medico = request.user.medico
        disponibilidad = get_object_or_404(DisponibilidadMedica, id=disponibilidad_id, medico=medico)
        
        if request.method == 'POST':
            form = DisponibilidadMedicaForm(request.POST, instance=disponibilidad)
            if form.is_valid():
                form.save()
                messages.success(request, 'Disponibilidad actualizada correctamente.')
                return redirect('disponibilidad_medica')
        else:
            form = DisponibilidadMedicaForm(instance=disponibilidad)
        
        context = {
            'form': form,
            'disponibilidad': disponibilidad,
            'dias_semana': DIAS_SEMANA_CHOICES,
            'tipos_turno': TIPO_TURNO_CHOICES,
        }
        
        return render(request, 'medico/editar_disponibilidad.html', context)
    except Exception as e:
        messages.error(request, f'Error al editar la disponibilidad: {str(e)}')
        return redirect('disponibilidad_medica')

@login_required
def desactivar_disponibilidad(request, disponibilidad_id):
    """Vista para desactivar una disponibilidad"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        medico = request.user.medico
        disponibilidad = get_object_or_404(DisponibilidadMedica, id=disponibilidad_id, medico=medico)
        
        disponibilidad.activo = False
        disponibilidad.save()
        
        messages.success(request, 'Disponibilidad desactivada correctamente.')
        return redirect('disponibilidad_medica')
    except Exception as e:
        messages.error(request, f'Error al desactivar la disponibilidad: {str(e)}')
        return redirect('disponibilidad_medica')

@login_required
def activar_disponibilidad(request, disponibilidad_id):
    """Vista para reactivar una disponibilidad"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        medico = request.user.medico
        disponibilidad = get_object_or_404(DisponibilidadMedica, id=disponibilidad_id, medico=medico)
        
        # Validar que no haya solapamiento con otras disponibilidades activas
        if disponibilidad.fecha_especial:
            # Validar solapamiento para fecha específica
            solapamiento = medico.disponibilidades.filter(
                fecha_especial=disponibilidad.fecha_especial,
                activo=True
            ).filter(
                Q(hora_inicio__lt=disponibilidad.hora_fin) & 
                Q(hora_fin__gt=disponibilidad.hora_inicio)
            ).exists()
        else:
            # Validar solapamiento para día de semana
            solapamiento = medico.disponibilidades.filter(
                dia_semana=disponibilidad.dia_semana,
                fecha_especial__isnull=True,
                activo=True
            ).filter(
                Q(hora_inicio__lt=disponibilidad.hora_fin) & 
                Q(hora_fin__gt=disponibilidad.hora_inicio)
            ).exists()
        
        if solapamiento:
            messages.error(request, 'No se puede activar este horario porque se solapa con otro horario existente.')
        else:
            disponibilidad.activo = True
            disponibilidad.save()
            messages.success(request, 'Disponibilidad activada correctamente.')
        
        return redirect('disponibilidad_medica')
    except Exception as e:
        messages.error(request, f'Error al activar la disponibilidad: {str(e)}')
        return redirect('disponibilidad_medica')

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_disponibilidades_medico(request):
    """API para obtener las disponibilidades del médico en formato JSON"""
    try:
        # Verificar que el usuario tenga rol de médico
        if not request.user.rol or request.user.rol.nombre != 'Medico':
            return JsonResponse({'success': False, 'error': 'No tienes permiso para acceder a esta información'}, status=403)
        
        medico = request.user.medico
        
        # Obtener disponibilidades regulares (por día de semana)
        disponibilidades_regulares = medico.disponibilidades.filter(
            fecha_especial__isnull=True,
            activo=True
        ).order_by('dia_semana', 'hora_inicio')
        
        # Obtener disponibilidades especiales (fechas específicas)
        disponibilidades_especiales = medico.disponibilidades.filter(
            fecha_especial__isnull=False,
            activo=True
        ).order_by('fecha_especial', 'hora_inicio')
        
        # Preparar datos para la respuesta
        regulares_data = []
        for disp in disponibilidades_regulares:
            regulares_data.append({
                'id': disp.id,
                'dia_semana': disp.dia_semana,
                'dia_nombre': dict(DIAS_SEMANA_CHOICES)[disp.dia_semana],
                'hora_inicio': disp.hora_inicio.strftime('%H:%M'),
                'hora_fin': disp.hora_fin.strftime('%H:%M'),
                'tipo_turno': disp.tipo_turno,
            })
        
        especiales_data = []
        for disp in disponibilidades_especiales:
            especiales_data.append({
                'id': disp.id,
                'fecha': disp.fecha_especial.strftime('%Y-%m-%d'),
                'fecha_formato': disp.fecha_especial.strftime('%d/%m/%Y'),
                'hora_inicio': disp.hora_inicio.strftime('%H:%M'),
                'hora_fin': disp.hora_fin.strftime('%H:%M'),
                'tipo_turno': disp.tipo_turno,
            })
        
        return JsonResponse({
            'success': True,
            'regulares': regulares_data,
            'especiales': especiales_data
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
