from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from .models import Paciente, HistorialMedico, Derivacion, Cita, DatosAntropometricos
from .forms import DatosAntropometricosForm
from .decorators import medico_required

@login_required
@medico_required
def historial_medico(request):
    """
    Vista que permite a los médicos ver el historial médico de pacientes
    que han atendido. Incluye:
    - Historial de atenciones médicas
    - Derivaciones realizadas
    - Historial de citas
    """
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
        
        # Obtener datos antropométricos del paciente
        datos_antropometricos = DatosAntropometricos.objects.filter(
            paciente=paciente
        ).order_by('-fecha_registro')
        
        # Formulario para registrar nuevos datos antropométricos
        form_antropometricos = DatosAntropometricosForm()
        
        # Si no hay historial, mostrar mensaje informativo
        if not historial.exists() and not derivaciones.exists() and not citas_previas.exists() and not datos_antropometricos.exists():
            messages.info(request, "Este paciente aún no tiene registros médicos en el sistema.")
    
    # Renderizar plantilla con los datos obtenidos
    return render(request, 'medico/historial_medico.html', {
        'paciente': paciente,
        'historial': historial,
        'derivaciones': derivaciones,
        'citas_previas': citas_previas,
        'datos_antropometricos': datos_antropometricos if paciente else [],
        'form_antropometricos': form_antropometricos if paciente else None,
        'query': query,
    })


@login_required
def registrar_datos_antropometricos(request, paciente_id):
    """
    Vista para registrar nuevos datos antropométricos de un paciente
    """
    # Verificar permisos (solo médicos pueden registrar datos)
    if not hasattr(request.user, 'medico') and not request.user.rol.nombre == 'Administrador':
        messages.error(request, "No tienes permisos para realizar esta acción.")
        return redirect('dashboard')
    
    # Obtener el paciente
    paciente = get_object_or_404(Paciente, id=paciente_id)
    
    if request.method == 'POST':
        form = DatosAntropometricosForm(request.POST)
        if form.is_valid():
            # Crear el registro pero no guardar aún
            datos = form.save(commit=False)
            datos.paciente = paciente
            datos.registrado_por = request.user
            
            # Asignar el médico que registra los datos
            if hasattr(request.user, 'medico'):
                datos.medico = request.user.medico
            
            # Si hay una cita en curso, asociarla
            cita_id = request.POST.get('cita_id')
            if cita_id:
                try:
                    cita = Cita.objects.get(id=cita_id)
                    datos.cita = cita
                except Cita.DoesNotExist:
                    pass
            
            # Guardar los datos
            datos.save()
            
            messages.success(request, "Datos antropométricos registrados correctamente.")
            
            # Redirigir al historial del paciente
            return redirect(f'historial_medico?paciente_id={paciente_id}')
        else:
            messages.error(request, "Error al registrar los datos. Por favor, verifica la información.")
    
    # Si no es POST o el formulario no es válido, redirigir al historial
    return redirect(f'historial_medico?paciente_id={paciente_id}')
