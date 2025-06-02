from django.shortcuts import render, get_object_or_404, redirect
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente, Cita, HistorialMedico, DatosAntropometricos
from .decorators import admin_required

@login_required
@admin_required
def admin_historial_medico(request):
    """
    Vista para que el administrador pueda ver el historial médico de todos los pacientes.
    """
    # Obtener todos los pacientes que tengan al menos una cita
    pacientes_con_historial = Paciente.objects.filter(
        Q(citas__isnull=False) | Q(historiales__isnull=False) | Q(datos_antropometricos__isnull=False)
    ).distinct()
    
    # Si se proporciona un ID de paciente, mostrar su historial
    paciente_id = request.GET.get('paciente_id')
    paciente_seleccionado = None
    citas = []
    historial = []
    datos_antropometricos = []
    
    if paciente_id:
        paciente_seleccionado = get_object_or_404(Paciente, id=paciente_id)
        citas = Cita.objects.filter(paciente=paciente_seleccionado).order_by('-fecha', '-hora_inicio')
        historial = HistorialMedico.objects.filter(paciente=paciente_seleccionado).order_by('-fecha')
        datos_antropometricos = DatosAntropometricos.objects.filter(paciente=paciente_seleccionado).order_by('-fecha_registro')
    
    context = {
        'pacientes': pacientes_con_historial,
        'paciente_seleccionado': paciente_seleccionado,
        'citas': citas,
        'historial': historial,
        'datos_antropometricos': datos_antropometricos,
    }
    
    return render(request, 'admin/historial_medico.html', context)
