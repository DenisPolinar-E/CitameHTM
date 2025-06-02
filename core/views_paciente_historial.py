from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Paciente, HistorialMedico, Derivacion, Cita, DatosAntropometricos
from .decorators import paciente_required

@login_required
@paciente_required
def mi_historial_medico(request):
    """
    Vista que permite a los pacientes ver su propio historial médico.
    Incluye:
    - Historial de atenciones médicas
    - Derivaciones recibidas
    - Historial de citas
    - Datos antropométricos (peso, talla, IMC)
    """
    paciente = request.user.paciente
    
    # Obtener historial médico completo del paciente
    historial = HistorialMedico.objects.filter(paciente=paciente).order_by('-fecha')
    
    # Obtener todas las derivaciones del paciente
    derivaciones = Derivacion.objects.filter(
        paciente=paciente
    ).order_by('-fecha_derivacion')
    
    # Obtener todas las citas del paciente
    citas = Cita.objects.filter(
        paciente=paciente
    ).order_by('-fecha')
    
    # Separar citas por estado
    citas_pendientes = citas.filter(estado__in=['pendiente', 'confirmada'])
    citas_atendidas = citas.filter(estado='atendida')
    citas_canceladas = citas.filter(estado='cancelada')
    
    # Obtener datos antropométricos del paciente
    datos_antropometricos = DatosAntropometricos.objects.filter(
        paciente=paciente
    ).order_by('-fecha_registro')
    
    # Obtener el último registro antropométrico (si existe)
    ultimo_registro = datos_antropometricos.first()
    
    # Si no hay historial, mostrar mensaje informativo
    if not historial.exists() and not derivaciones.exists() and not citas.exists() and not datos_antropometricos.exists():
        messages.info(request, "Aún no tienes registros médicos en el sistema.")
    
    # Renderizar plantilla con los datos obtenidos
    return render(request, 'paciente/mi_historial_medico.html', {
        'historial': historial,
        'derivaciones': derivaciones,
        'citas_pendientes': citas_pendientes,
        'citas_atendidas': citas_atendidas,
        'citas_canceladas': citas_canceladas,
        'datos_antropometricos': datos_antropometricos,
        'ultimo_registro': ultimo_registro,
    })
