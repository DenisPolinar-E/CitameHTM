from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Paciente, HistorialMedico, Derivacion, Cita

@login_required
def historial_medico(request):
    """
    Vista que permite a los médicos ver el historial médico de pacientes
    que han atendido. Incluye:
    - Historial de atenciones médicas
    - Derivaciones realizadas
    - Historial de citas
    """
    # Verificar que el usuario sea médico
    if not hasattr(request.user, 'medico'):
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('dashboard')
    
    medico = request.user.medico
    
    # Buscar paciente por DNI o nombre
    query = request.GET.get('q', '')
    paciente_id = request.GET.get('paciente_id', '')
    
    # Inicializar variables
    paciente = None
    historial = []
    derivaciones = []
    citas_previas = []
    
    # Si hay búsqueda por nombre/DNI o ID específico
    if query or paciente_id:
        if paciente_id:
            # Buscar por ID específico
            paciente = get_object_or_404(Paciente, id=paciente_id)
        else:
            # Buscar pacientes que coincidan con la búsqueda
            pacientes = Paciente.objects.filter(
                Q(usuario__nombres__icontains=query) | 
                Q(usuario__apellidos__icontains=query) |
                Q(usuario__dni__icontains=query)
            )
            
            if pacientes.count() == 1:
                paciente = pacientes.first()
            elif pacientes.count() > 1:
                # Si hay múltiples coincidencias, mostrar resultados para elegir
                return render(request, 'medico/historial_medico.html', {
                    'query': query,
                    'resultados_busqueda': pacientes,
                })
            else:
                messages.warning(request, f"No se encontraron pacientes con el criterio: {query}")
    
    # Si tenemos un paciente específico, mostrar su historial
    if paciente:
        # Obtener historial médico completo del paciente
        historial = HistorialMedico.objects.filter(paciente=paciente).order_by('-fecha')
        
        # Obtener todas las derivaciones del paciente
        derivaciones = Derivacion.objects.filter(
            paciente=paciente
        ).order_by('-fecha_derivacion')
        
        # Obtener todas las citas atendidas del paciente
        citas_previas = Cita.objects.filter(
            paciente=paciente,
            estado='atendida'
        ).order_by('-fecha')
        
        # Si no hay historial, mostrar mensaje informativo
        if not historial.exists() and not derivaciones.exists() and not citas_previas.exists():
            messages.info(request, "Este paciente aún no tiene registros médicos en el sistema.")
    
    # Renderizar plantilla con los datos obtenidos
    return render(request, 'medico/historial_medico.html', {
        'paciente': paciente,
        'historial': historial,
        'derivaciones': derivaciones,
        'citas_previas': citas_previas,
        'query': query,
    })
