from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.db.models import Q
from django.utils import timezone
from django.http import JsonResponse
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from datetime import datetime, timedelta

from .models import Paciente, Especialidad, Medico, Consultorio, Cita, Derivacion, Notificacion, DisponibilidadMedica
from .utils_notificaciones import crear_notificacion

@login_required
def reservar_cita(request):
    """Vista para que los pacientes reserven citas"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Paciente':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        paciente = request.user.paciente
        
        # Verificar si el paciente está bloqueado
        if paciente.estado_reserva == 'bloqueado':
            messages.error(request, 'Su cuenta está bloqueada para reservar citas debido a inasistencias consecutivas. Por favor, contacte a admisión.')
            return redirect('dashboard_paciente')
        
        # Obtener especialidades disponibles
        especialidades = Especialidad.objects.filter(acceso_directo=True).order_by('nombre')
        derivaciones_activas = Derivacion.objects.filter(
            paciente=paciente,
            estado='pendiente',
            fecha_derivacion__gte=timezone.now().date() - timedelta(days=30)  # Derivaciones de los últimos 30 días
        )
        
        # Agregar especialidades de derivaciones activas
        especialidades_derivadas = Especialidad.objects.filter(
            id__in=derivaciones_activas.values_list('especialidad_destino', flat=True)
        )
        # Combinar QuerySets
        especialidades = (especialidades | especialidades_derivadas).distinct()
        
        # Variables para el formulario
        medicos = []
        horarios_disponibles = []
        especialidad_seleccionada = None
        medico_seleccionado = None
        fecha_seleccionada = None
        
        if request.method == 'POST':
            # Procesar el formulario de reserva
            especialidad_id = request.POST.get('especialidad')
            medico_id = request.POST.get('medico')
            fecha = request.POST.get('fecha')
            hora = request.POST.get('hora')
            motivo = request.POST.get('motivo')
            
            # Validaciones básicas
            if not all([especialidad_id, medico_id, fecha, hora, motivo]):
                messages.error(request, 'Todos los campos son obligatorios')
            else:
                try:
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
                        # Verificar si necesita derivación
                        especialidad = Especialidad.objects.get(id=especialidad_id)
                        derivacion = None
                        
                        if not especialidad.acceso_directo:
                            # Buscar derivación activa para esta especialidad
                            derivacion = derivaciones_activas.filter(especialidad_destino=especialidad).first()
                            
                            if not derivacion:
                                messages.error(request, 'Necesita una derivación para agendar en esta especialidad')
                                return redirect('reservar_cita')
                        
                        # Crear la cita
                        cita = Cita.objects.create(
                            paciente=paciente,
                            medico=medico,
                            consultorio=consultorio,
                            fecha=fecha_obj,
                            hora_inicio=hora_obj,
                            hora_fin=hora_fin,
                            estado='pendiente',
                            motivo=motivo,
                            reservado_por=request.user
                        )
                        
                        # Si había derivación, marcarla como usada
                        if derivacion:
                            derivacion.estado = 'usada'
                            derivacion.usada_en_cita = cita
                            derivacion.save()
                        
                        # Crear notificación para el paciente
                        crear_notificacion(
                            usuario=request.user,
                            mensaje=f'Su cita con {medico.usuario.nombres} {medico.usuario.apellidos} ha sido agendada para el {fecha_obj.strftime("%d/%m/%Y")} a las {hora_obj.strftime("%H:%M")}.',
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
                        
                        messages.success(request, 'Cita reservada exitosamente')
                        return redirect('dashboard_paciente')
                except Exception as e:
                    messages.error(request, f'Error al reservar la cita: {str(e)}')
            
            # Si hay errores, mantener los valores seleccionados
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
        
        # Para solicitudes GET o si hay errores en POST
        context = {
            'especialidades': especialidades,
            'medicos': medicos,
            'horarios_disponibles': horarios_disponibles,
            'especialidad_seleccionada': especialidad_seleccionada,
            'medico_seleccionado': medico_seleccionado,
            'fecha_seleccionada': fecha_seleccionada,
            'derivaciones_activas': derivaciones_activas,
            'fecha_minima': timezone.now().date().strftime('%Y-%m-%d'),
            'fecha_maxima': (timezone.now().date() + timedelta(days=60)).strftime('%Y-%m-%d')  # Permitir reservas hasta 2 meses adelante
        }
        
        return render(request, 'paciente/reservar_cita.html', context)
    
    except Paciente.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de paciente')
        return redirect('home')

def obtener_horarios_disponibles(medico, fecha_str):
    """Obtiene los horarios disponibles para un médico en una fecha específica"""
    try:
        fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
        
        # Obtener disponibilidad del médico para este día
        dia_semana = fecha.weekday()  # 0 es lunes, 6 es domingo
        disponibilidades = DisponibilidadMedica.objects.filter(
            medico=medico,
            activo=True
        ).filter(
            Q(dia_semana=dia_semana) | Q(fecha_especial=fecha)
        )
        
        if not disponibilidades.exists():
            return []
        
        # Obtener citas ya agendadas para este día
        citas_existentes = Cita.objects.filter(
            medico=medico,
            fecha=fecha,
            estado__in=['pendiente', 'confirmada']
        )
        
        # Generar bloques de 30 minutos dentro de la disponibilidad
        horarios_disponibles = []
        
        for disponibilidad in disponibilidades:
            hora_actual = disponibilidad.hora_inicio
            while hora_actual < disponibilidad.hora_fin:
                hora_fin_bloque = (datetime.combine(fecha, hora_actual) + timedelta(minutes=30)).time()
                
                # Verificar si este bloque se solapa con alguna cita existente
                bloque_disponible = True
                for cita in citas_existentes:
                    if (hora_actual < cita.hora_fin and hora_fin_bloque > cita.hora_inicio):
                        bloque_disponible = False
                        break
                
                if bloque_disponible and hora_fin_bloque <= disponibilidad.hora_fin:
                    horarios_disponibles.append(hora_actual.strftime('%H:%M'))
                
                # Avanzar 30 minutos
                hora_actual = (datetime.combine(fecha, hora_actual) + timedelta(minutes=30)).time()
        
        return sorted(horarios_disponibles)
    except Exception as e:
        print(f"Error al obtener horarios disponibles: {e}")
        return []


# API Views
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_medicos_por_especialidad(request, especialidad_id):
    """API para obtener médicos por especialidad"""
    try:
        # Verificar que el usuario tenga rol de paciente
        if not request.user.rol or request.user.rol.nombre != 'Paciente':
            return JsonResponse({'success': False, 'error': 'No tienes permiso para acceder a esta información'}, status=403)
        
        # Validar el ID de la especialidad
        try:
            especialidad_id = int(especialidad_id)
        except (ValueError, TypeError):
            return JsonResponse({'success': False, 'error': f'ID de especialidad inválido: {especialidad_id}'}, status=400)
        
        # Obtener la especialidad
        print(f"Buscando especialidad con ID: {especialidad_id}")
        try:
            especialidad = Especialidad.objects.get(id=especialidad_id)
            print(f"Especialidad encontrada: {especialidad.nombre}")
        except Especialidad.DoesNotExist:
            print(f"No se encontró la especialidad con ID: {especialidad_id}")
            return JsonResponse({'success': False, 'error': f'No se encontró la especialidad con ID: {especialidad_id}'}, status=404)
        
        # Obtener médicos de esta especialidad
        medicos = Medico.objects.filter(especialidad=especialidad)
        print(f"Médicos encontrados para {especialidad.nombre}: {medicos.count()}")
        
        # Listar los médicos encontrados para depuración
        for medico in medicos:
            print(f"Médico: {medico.usuario.nombres} {medico.usuario.apellidos}, ID: {medico.id}")
        
        # Preparar datos para la respuesta
        medicos_data = []
        for medico in medicos:
            try:
                medico_data = {
                    'id': medico.id,
                    'nombres': medico.usuario.nombres,
                    'apellidos': medico.usuario.apellidos,
                    'especialidad': medico.especialidad.nombre
                }
                medicos_data.append(medico_data)
            except Exception as e:
                print(f"Error al procesar médico {medico.id}: {str(e)}")
        
        print(f"Enviando respuesta con {len(medicos_data)} médicos")
        return JsonResponse({
            'success': True,
            'medicos': medicos_data,
            'especialidad': {
                'id': especialidad.id,
                'nombre': especialidad.nombre
            }
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)

@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_horarios_disponibles(request, medico_id, fecha):
    """API para obtener horarios disponibles para un médico en una fecha específica"""
    try:
        # Verificar que el usuario tenga rol de paciente
        if not request.user.rol or request.user.rol.nombre != 'Paciente':
            return JsonResponse({'success': False, 'error': 'No tienes permiso para acceder a esta información'}, status=403)
        
        # Obtener el médico
        medico = get_object_or_404(Medico, id=medico_id)
        
        # Obtener horarios disponibles
        horarios = obtener_horarios_disponibles(medico, fecha)
        
        return JsonResponse({
            'success': True,
            'horarios': horarios
        })
    except Exception as e:
        return JsonResponse({'success': False, 'error': str(e)}, status=500)
