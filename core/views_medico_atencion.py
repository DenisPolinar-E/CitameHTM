from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.http import JsonResponse
from django.db import transaction
from datetime import datetime
from .models import Cita, HistorialMedico, Derivacion, Especialidad, Notificacion, Medico, DisponibilidadMedica, Consultorio

@login_required
def atender_paciente(request, cita_id):
    """
    Vista para atender a un paciente y registrar la atención médica.
    Permite al médico:
    1. Ver los datos del paciente y la cita
    2. Registrar diagnóstico y tratamiento
    3. Derivar a un especialista si es necesario
    """
    # Verificar que el usuario sea médico
    if not hasattr(request.user, 'medico'):
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('dashboard')
    
    # Obtener la cita
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Verificar que la cita corresponda al médico actual
    if cita.medico.usuario != request.user:
        messages.error(request, "Esta cita no te corresponde.")
        return redirect('dashboard_medico')
    
    # Verificar que la cita esté en estado pendiente o confirmada
    if cita.estado not in ['pendiente', 'confirmada']:
        messages.error(request, f"No se puede atender esta cita porque su estado es: {cita.get_estado_display()}")
        return redirect('dashboard_medico')
    
    # Obtener especialidades para derivación
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Procesar el formulario de atención
    if request.method == 'POST':
        accion = request.POST.get('accion', '')
        
        if accion == 'atender':
            # Registrar la atención médica
            diagnostico = request.POST.get('diagnostico', '')
            tratamiento = request.POST.get('tratamiento', '')
            observaciones = request.POST.get('observaciones', '')
            
            if not diagnostico or not tratamiento:
                messages.error(request, "Debes completar el diagnóstico y tratamiento.")
                return render(request, 'medico/atencion_paciente.html', {
                    'cita': cita,
                    'especialidades': especialidades,
                })
            
            with transaction.atomic():
                # Actualizar estado de la cita
                cita.estado = 'atendida'
                cita.asistio = True
                cita.save()
                
                # Crear registro en historial médico
                HistorialMedico.objects.create(
                    paciente=cita.paciente,
                    fecha=timezone.now(),
                    diagnostico=diagnostico,
                    tratamiento=tratamiento,
                    observaciones=observaciones
                )
                
                # Crear notificación para el paciente
                Notificacion.objects.create(
                    usuario=cita.paciente.usuario,
                    mensaje=f"Tu cita con el Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos} ha sido registrada. Revisa tu historial médico para ver el diagnóstico y tratamiento.",
                    tipo='informacion',
                    importante=True
                )
            
            messages.success(request, "Atención médica registrada correctamente.")
            return redirect('dashboard_medico')
            
        elif accion == 'derivar':
            # MODIFICACIÓN TEMPORAL: Permitir derivar sin completar atención
            # Marcar la cita como atendida automáticamente
            if cita.estado != 'atendida':
                with transaction.atomic():
                    # Actualizar estado de la cita
                    cita.estado = 'atendida'
                    cita.asistio = True
                    cita.save()
                    
                    # Crear registro básico en historial médico
                    HistorialMedico.objects.create(
                        paciente=cita.paciente,
                        fecha=timezone.now(),
                        diagnostico="Atención completada automáticamente para pruebas",
                        tratamiento="N/A - Prueba de sistema",
                        observaciones="Registro automático para pruebas de derivación"
                    )
                    
                    messages.info(request, "Atención médica registrada automáticamente para pruebas.")
                # Continuar con la derivación
                
            # Registrar la derivación a especialista
            especialidad_id = request.POST.get('especialidad', '')
            motivo_derivacion = request.POST.get('motivo_derivacion', '')
            vigencia_dias = request.POST.get('vigencia_dias', '30')
            
            if not especialidad_id or not motivo_derivacion:
                messages.error(request, "Debes seleccionar una especialidad y especificar el motivo de la derivación.")
                return render(request, 'medico/atencion_paciente.html', {
                    'cita': cita,
                    'especialidades': especialidades,
                })
            
            try:
                especialidad = Especialidad.objects.get(id=especialidad_id)
                vigencia = int(vigencia_dias)
                
                with transaction.atomic():
                    # Crear la derivación
                    derivacion = Derivacion.objects.create(
                        paciente=cita.paciente,
                        medico_origen=cita.medico,
                        especialidad_destino=especialidad,
                        fecha_derivacion=timezone.now().date(),
                        motivo=motivo_derivacion,
                        vigencia_dias=vigencia,
                        estado='pendiente'
                    )
                    
                    # Crear notificación para el paciente
                    Notificacion.objects.create(
                        usuario=cita.paciente.usuario,
                        mensaje=f"Has sido derivado a la especialidad de {especialidad.nombre} por el Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos}. Por favor, reserva una cita con un especialista.",
                        tipo='informacion',
                        importante=True
                    )
                
                messages.success(request, f"Paciente derivado correctamente a {especialidad.nombre}.")
                return redirect('dashboard_medico')
                
            except Especialidad.DoesNotExist:
                messages.error(request, "La especialidad seleccionada no existe.")
            except ValueError:
                messages.error(request, "El valor de vigencia debe ser un número entero.")
    
    # Renderizar la plantilla con los datos de la cita
    return render(request, 'medico/atencion_paciente.html', {
        'cita': cita,
        'especialidades': especialidades,
    })

@login_required
def derivar_paciente(request, cita_id):
    """
    Vista específica para derivar a un paciente a un especialista
    y agendar directamente la cita con el especialista si se desea.
    """
    # Verificar que el usuario sea médico
    if not hasattr(request.user, 'medico'):
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('dashboard')
    
    # Obtener la cita
    cita = get_object_or_404(Cita, id=cita_id)
    
    # Verificar que la cita corresponda al médico actual
    if cita.medico.usuario != request.user:
        messages.error(request, "Esta cita no te corresponde.")
        return redirect('dashboard_medico')
    
    # Obtener especialidades para derivación
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Procesar el formulario de derivación
    if request.method == 'POST':
        especialidad_id = request.POST.get('especialidad', '')
        motivo_derivacion = request.POST.get('motivo_derivacion', '')
        vigencia_dias = request.POST.get('vigencia_dias', '30')
        
        # Datos para el agendamiento directo de cita
        medico_especialista_id = request.POST.get('medico_especialista', '')
        fecha_cita = request.POST.get('fecha_cita', '')
        horario_id = request.POST.get('horario_cita', '')
        consultorio_codigo = request.POST.get('consultorio', '')
        
        if not especialidad_id or not motivo_derivacion:
            messages.error(request, "Debes seleccionar una especialidad y especificar el motivo de la derivación.")
            return render(request, 'medico/derivar_paciente.html', {
                'cita': cita,
                'especialidades': especialidades,
            })
        
        try:
            especialidad = Especialidad.objects.get(id=especialidad_id)
            vigencia = int(vigencia_dias)
            
            with transaction.atomic():
                # Crear la derivación
                derivacion = Derivacion.objects.create(
                    paciente=cita.paciente,
                    medico_origen=cita.medico,
                    especialidad_destino=especialidad,
                    fecha_derivacion=timezone.now().date(),
                    motivo=motivo_derivacion,
                    vigencia_dias=vigencia,
                    estado='pendiente'
                )
                
                # Si se proporcionaron datos para agendar cita
                if medico_especialista_id and fecha_cita and horario_id:
                    try:
                        # Obtener el médico especialista
                        medico_especialista = Medico.objects.get(id=medico_especialista_id)
                        
                        # Obtener la disponibilidad seleccionada
                        disponibilidad = DisponibilidadMedica.objects.get(id=horario_id)
                        
                        # Convertir la fecha string a objeto date
                        fecha_obj = datetime.strptime(fecha_cita, '%Y-%m-%d').date()
                        
                        # Buscar o crear consultorio
                        consultorio, _ = Consultorio.objects.get_or_create(
                            codigo=consultorio_codigo,
                            defaults={'piso': '1', 'area': 'Consulta Externa'}
                        )
                        
                        # Crear la cita con el especialista
                        nueva_cita = Cita.objects.create(
                            paciente=cita.paciente,
                            medico=medico_especialista,
                            consultorio=consultorio,
                            fecha=fecha_obj,
                            hora_inicio=disponibilidad.hora_inicio,
                            hora_fin=disponibilidad.hora_fin,
                            motivo=f"Derivación: {motivo_derivacion}",
                            estado='pendiente',
                            derivacion=derivacion,
                            reservado_por=request.user
                        )
                        
                        # Actualizar estado de la derivación
                        derivacion.estado = 'usada'
                        derivacion.cita_agendada = True
                        derivacion.save()
                        
                        # Notificar al paciente sobre la cita agendada
                        Notificacion.objects.create(
                            usuario=cita.paciente.usuario,
                            mensaje=f"Se ha agendado una cita con el especialista Dr. {medico_especialista.usuario.nombres} {medico_especialista.usuario.apellidos} para el {fecha_obj.strftime('%d/%m/%Y')} a las {disponibilidad.hora_inicio.strftime('%H:%M')} en el consultorio {consultorio.codigo}.",
                            tipo='confirmacion',
                            importante=True
                        )
                        
                        messages.success(request, f"Paciente derivado y cita agendada correctamente con {medico_especialista.usuario.nombres} {medico_especialista.usuario.apellidos} para el {fecha_obj.strftime('%d/%m/%Y')}.")
                    except Exception as e:
                        # Si hay error en el agendamiento, solo crear la derivación
                        messages.warning(request, f"Paciente derivado pero no se pudo agendar la cita: {str(e)}")
                        
                        # Crear notificación para el paciente (solo derivación)
                        Notificacion.objects.create(
                            usuario=cita.paciente.usuario,
                            mensaje=f"Has sido derivado a la especialidad de {especialidad.nombre} por el Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos}. Por favor, reserva una cita con un especialista.",
                            tipo='informacion',
                            importante=True
                        )
                else:
                    # Crear notificación para el paciente (solo derivación)
                    Notificacion.objects.create(
                        usuario=cita.paciente.usuario,
                        mensaje=f"Has sido derivado a la especialidad de {especialidad.nombre} por el Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos}. Por favor, reserva una cita con un especialista.",
                        tipo='informacion',
                        importante=True
                    )
                    messages.success(request, f"Paciente derivado correctamente a {especialidad.nombre}.")
                
                return redirect('dashboard_medico')
            
        except Especialidad.DoesNotExist:
            messages.error(request, "La especialidad seleccionada no existe.")
        except ValueError:
            messages.error(request, "El valor de vigencia debe ser un número entero.")
        except Exception as e:
            messages.error(request, f"Error al procesar la derivación: {str(e)}")
    
    # Renderizar la plantilla de derivación
    return render(request, 'medico/derivar_paciente.html', {
        'cita': cita,
        'especialidades': especialidades,
    })

@login_required
def ver_derivaciones(request):
    """
    Vista para que el médico vea las derivaciones que ha realizado
    """
    # Verificar que el usuario sea médico
    if not hasattr(request.user, 'medico'):
        messages.error(request, "No tienes permisos para acceder a esta página.")
        return redirect('dashboard')
    
    # Obtener las derivaciones realizadas por el médico
    derivaciones = Derivacion.objects.filter(
        medico_origen=request.user.medico
    ).order_by('-fecha_derivacion')
    
    return render(request, 'medico/ver_derivaciones.html', {
        'derivaciones': derivaciones,
    })
