from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta
import json

from .models import Paciente, Especialidad, Medico, Consultorio, Cita, Derivacion, Notificacion, DisponibilidadMedica, Usuario
from .decorators import admision_required
from .views_paciente import obtener_horarios_disponibles
from .utils_notificaciones import crear_notificacion

@login_required
@admision_required
def registrar_cita(request):
    """Vista para que el personal de admisión registre citas para pacientes"""
    
    # Obtener especialidades disponibles
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Variables para el formulario
    pacientes = []
    medicos = []
    horarios_disponibles = []
    paciente_seleccionado = None
    especialidad_seleccionada = None
    medico_seleccionado = None
    fecha_seleccionada = None
    
    # Buscar paciente si se ha enviado una consulta
    query = request.GET.get('q', '')
    if query:
        pacientes = Paciente.objects.filter(
            Q(usuario__nombres__icontains=query) | 
            Q(usuario__apellidos__icontains=query) | 
            Q(usuario__dni__icontains=query)
        )[:10]  # Limitar a 10 resultados
    
    if request.method == 'POST':
        # Procesar el formulario de reserva
        paciente_id = request.POST.get('paciente')
        especialidad_id = request.POST.get('especialidad')
        medico_id = request.POST.get('medico')
        fecha = request.POST.get('fecha')
        hora = request.POST.get('hora')
        motivo = request.POST.get('motivo')
        
        # Validaciones básicas
        if not all([paciente_id, especialidad_id, medico_id, fecha, hora, motivo]):
            messages.error(request, 'Todos los campos son obligatorios')
        else:
            try:
                # Obtener el paciente
                paciente = Paciente.objects.get(id=paciente_id)
                
                # Convertir fecha y hora
                fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
                hora_obj = datetime.strptime(hora, '%H:%M').time()
                
                # Calcular hora de fin (30 minutos después)
                hora_fin = (datetime.combine(fecha_obj, hora_obj) + timedelta(minutes=30)).time()
                
                # Obtener médico y consultorio
                medico = Medico.objects.get(id=medico_id)
                consultorio = Consultorio.objects.first()  # Simplificado para el ejemplo
                
                # Verificar disponibilidad
                citas_existentes = Cita.objects.filter(
                    medico=medico,
                    fecha=fecha_obj,
                    estado__in=['pendiente', 'confirmada'],
                    hora_inicio__lt=hora_fin,
                    hora_fin__gt=hora_obj
                )
                
                if citas_existentes.exists():
                    messages.error(request, 'El horario seleccionado ya no está disponible. Por favor, elija otro.')
                else:
                    # Crear la cita
                    cita = Cita.objects.create(
                        paciente=paciente,
                        medico=medico,
                        consultorio=consultorio,
                        fecha=fecha_obj,
                        hora_inicio=hora_obj,
                        hora_fin=hora_fin,
                        estado='confirmada',  # Las citas registradas por admisión se crean como confirmadas
                        motivo=motivo,
                        reservado_por=request.user
                    )
                    
                    # Crear notificación para el paciente
                    crear_notificacion(
                        usuario=paciente.usuario,
                        mensaje=f'Se ha registrado una cita con {medico.usuario.nombres} {medico.usuario.apellidos} para el {fecha_obj.strftime("%d/%m/%Y")} a las {hora_obj.strftime("%H:%M")}.',
                        tipo='confirmacion',
                        importante=True,
                        objeto_relacionado='cita',
                        objeto_id=cita.id,
                        creador=request.user
                    )
                    
                    # Crear notificación para el médico
                    crear_notificacion(
                        usuario=medico.usuario,
                        mensaje=f'Nueva cita agendada con {paciente.usuario.nombres} {paciente.usuario.apellidos} para el {fecha_obj.strftime("%d/%m/%Y")} a las {hora_obj.strftime("%H:%M")}.',
                        tipo='informacion',
                        objeto_relacionado='cita',
                        objeto_id=cita.id,
                        creador=request.user
                    )
                    
                    messages.success(request, 'Cita registrada exitosamente')
                    return redirect('registrar_cita')
            except Exception as e:
                messages.error(request, f'Error al registrar la cita: {str(e)}')
        
        # Si hay errores, mantener los valores seleccionados
        if paciente_id:
            paciente_seleccionado = Paciente.objects.get(id=paciente_id)
        
        if especialidad_id:
            especialidad_seleccionada = Especialidad.objects.get(id=especialidad_id)
            medicos = Medico.objects.filter(especialidad=especialidad_seleccionada)
        
        if medico_id:
            medico_seleccionado = Medico.objects.get(id=medico_id)
        
        if fecha:
            fecha_seleccionada = fecha
            if medico_seleccionado:
                # Obtener horarios disponibles para esta fecha y médico
                horarios_disponibles = obtener_horarios_disponibles(medico_seleccionado, fecha)
    
    context = {
        'pacientes': pacientes,
        'especialidades': especialidades,
        'medicos': medicos,
        'horarios_disponibles': horarios_disponibles,
        'paciente_seleccionado': paciente_seleccionado,
        'especialidad_seleccionada': especialidad_seleccionada,
        'medico_seleccionado': medico_seleccionado,
        'fecha_seleccionada': fecha_seleccionada,
        'query': query
    }
    
    return render(request, 'admision/registrar_cita.html', context)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def buscar_pacientes_api(request):
    """API para buscar pacientes por nombre, apellido o DNI"""
    query = request.GET.get('q', '')
    if not query or len(query) < 3:
        return JsonResponse({'results': []})
    
    pacientes = Paciente.objects.filter(
        Q(usuario__nombres__icontains=query) | 
        Q(usuario__apellidos__icontains=query) | 
        Q(usuario__dni__icontains=query)
    )[:10]
    
    results = [{
        'id': paciente.id,
        'nombre': f"{paciente.usuario.nombres} {paciente.usuario.apellidos}",
        'dni': paciente.usuario.dni,
        'fecha_nacimiento': paciente.usuario.fecha_nacimiento.strftime('%d/%m/%Y') if paciente.usuario.fecha_nacimiento else '',
    } for paciente in pacientes]
    
    return JsonResponse({'results': results})
