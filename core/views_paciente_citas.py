from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import HttpResponseForbidden
from .models import Cita, Paciente, Notificacion

@login_required
def mis_citas(request):
    """
    Vista para mostrar las citas del paciente en formato de tarjetas.
    Permite filtrar por estado y fecha.
    """
    # Verificar que el usuario es un paciente
    if not hasattr(request.user, 'paciente'):
        messages.error(request, "Solo los pacientes pueden acceder a esta sección.")
        return redirect('dashboard')
    
    paciente = request.user.paciente
    
    # Obtener parámetros de filtro
    estado_filtro = request.GET.get('estado', 'todas')
    fecha_filtro = request.GET.get('fecha', 'todas')
    
    # Filtrar citas por paciente
    citas = Cita.objects.filter(paciente=paciente)
    
    # Aplicar filtro de estado
    if estado_filtro != 'todas':
        citas = citas.filter(estado=estado_filtro)
    
    # Aplicar filtro de fecha
    hoy = timezone.now().date()
    if fecha_filtro == 'pendientes':
        citas = citas.filter(fecha__gte=hoy)
    elif fecha_filtro == 'pasadas':
        citas = citas.filter(fecha__lt=hoy)
    
    # Ordenar citas (primero las más recientes)
    citas = citas.order_by('-fecha', '-hora_inicio')
    
    # Estadísticas para mostrar en la vista
    total_citas = citas.count()
    citas_pendientes = Cita.objects.filter(
        paciente=paciente,
        fecha__gte=hoy,
        estado__in=['pendiente', 'confirmada']
    ).count()
    citas_completadas = Cita.objects.filter(
        paciente=paciente,
        estado='atendida'
    ).count()
    citas_canceladas = Cita.objects.filter(
        paciente=paciente,
        estado='cancelada'
    ).count()
    
    # Renderizar plantilla
    return render(request, 'paciente/mis_citas.html', {
        'citas': citas,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_completadas': citas_completadas,
        'citas_canceladas': citas_canceladas,
        'estado_filtro': estado_filtro,
        'fecha_filtro': fecha_filtro
    })

@login_required
def cancelar_cita(request, cita_id):
    """
    Vista para cancelar una cita programada.
    Solo permite cancelar citas propias que estén en estado pendiente o confirmada.
    """
    # Obtener la cita o retornar 404
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Verificar que el usuario es el propietario de la cita
    if not hasattr(request.user, 'paciente') or cita.paciente.id != request.user.paciente.id:
        return HttpResponseForbidden("No tienes permiso para cancelar esta cita.")
    
    # Verificar que la cita está en estado pendiente o confirmada
    if cita.estado not in ['pendiente', 'confirmada']:
        messages.error(request, "Solo se pueden cancelar citas pendientes o confirmadas.")
        return redirect('mis_citas')
    
    # Verificar que la cita no sea para hoy o una fecha pasada
    hoy = timezone.now().date()
    if cita.fecha <= hoy:
        messages.error(request, "No se pueden cancelar citas para hoy o fechas pasadas.")
        return redirect('mis_citas')
    
    # Cambiar el estado de la cita a cancelada
    cita.estado = 'cancelada'
    cita.save()
    
    # Crear notificación para el médico
    Notificacion.objects.create(
        usuario=cita.medico.usuario,
        mensaje=f"El paciente {cita.paciente.usuario.nombres} {cita.paciente.usuario.apellidos} ha cancelado su cita del {cita.fecha.strftime('%d/%m/%Y')} a las {cita.hora_inicio.strftime('%H:%M')}.",
        tipo='cancelacion',
        leido=False,
        importante=True,
        objeto_relacionado='cita',
        objeto_id=cita.id
    )
    
    messages.success(request, "La cita ha sido cancelada correctamente.")
    return redirect('mis_citas')
