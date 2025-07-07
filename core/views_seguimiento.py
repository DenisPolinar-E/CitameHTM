from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
from .models import (
    Paciente, Medico, Cita, TratamientoProgramado, 
    SeguimientoSesion, Consultorio, Notificacion
)
from .forms import TratamientoProgramadoForm

@login_required
def programar_seguimientos(request):
    """Vista para programar nuevos tratamientos con seguimiento"""
    # Verificar que el usuario tenga el rol correcto (médico)
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener el médico asociado al usuario
    try:
        medico = request.user.medico
    except Medico.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de médico')
        return redirect('dashboard')
    
    # Procesar el formulario si es POST
    if request.method == 'POST':
        form = TratamientoProgramadoForm(request.POST)
        if form.is_valid():
            # Guardar el tratamiento pero no commit aún
            tratamiento = form.save(commit=False)
            tratamiento.medico = medico
            tratamiento.save()
            
            # Crear las sesiones de seguimiento
            fecha_sesion = tratamiento.fecha_inicio
            for i in range(1, tratamiento.cantidad_sesiones + 1):
                SeguimientoSesion.objects.create(
                    tratamiento=tratamiento,
                    numero_sesion=i,
                    fecha_programada=fecha_sesion,
                    estado='pendiente'
                )
                # Calcular la fecha de la siguiente sesión
                fecha_sesion = fecha_sesion + timedelta(days=tratamiento.frecuencia_dias)
            
            # Crear notificación para el paciente
            Notificacion.objects.create(
                usuario=tratamiento.paciente.usuario,
                mensaje=f"Se ha programado un nuevo tratamiento con {tratamiento.cantidad_sesiones} sesiones.",
                tipo='informacion',
                importante=True,
                url_redireccion=f'/mis-tratamientos/{tratamiento.id}/',
                objeto_relacionado='tratamiento',
                objeto_id=tratamiento.id
            )
            
            messages.success(request, f'Tratamiento programado exitosamente con {tratamiento.cantidad_sesiones} sesiones')
            return redirect('ver_seguimientos')
    else:
        form = TratamientoProgramadoForm()
    
    # Obtener lista de pacientes para el formulario
    pacientes = Paciente.objects.all().order_by('usuario__apellidos')
    
    context = {
        'form': form,
        'pacientes': pacientes,
    }
    
    return render(request, 'medico/programar_seguimiento.html', context)

@login_required
def ver_seguimientos(request):
    """Vista para ver todos los tratamientos programados"""
    # Verificar que el usuario tenga el rol correcto (médico)
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener el médico asociado al usuario
    try:
        medico = request.user.medico
    except Medico.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de médico')
        return redirect('dashboard')
    
    # Obtener tratamientos filtrados por estado si se especifica
    estado_filtro = request.GET.get('estado', None)
    
    tratamientos = TratamientoProgramado.objects.filter(medico=medico)
    if estado_filtro:
        tratamientos = tratamientos.filter(estado=estado_filtro)
    
    tratamientos = tratamientos.order_by('-created_at')
    
    context = {
        'tratamientos': tratamientos,
        'estado_filtro': estado_filtro,
    }
    
    return render(request, 'medico/ver_seguimientos.html', context)

@login_required
def detalle_seguimiento(request, tratamiento_id):
    """Vista para ver el detalle de un tratamiento y sus sesiones"""
    # Verificar que el usuario tenga el rol correcto (médico o paciente)
    if not request.user.rol or request.user.rol.nombre not in ['Medico', 'Paciente']:
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener el tratamiento
    tratamiento = get_object_or_404(TratamientoProgramado, id=tratamiento_id)
    
    # Verificar permisos (solo el médico asignado o el paciente pueden ver)
    es_medico_asignado = False
    es_paciente_asignado = False
    
    if request.user.rol.nombre == 'Medico':
        try:
            if request.user.medico == tratamiento.medico:
                es_medico_asignado = True
        except Medico.DoesNotExist:
            pass
    
    if request.user.rol.nombre == 'Paciente':
        try:
            if request.user.paciente == tratamiento.paciente:
                es_paciente_asignado = True
        except Paciente.DoesNotExist:
            pass
    
    if not (es_medico_asignado or es_paciente_asignado):
        messages.error(request, 'No tienes permiso para ver este tratamiento')
        return redirect('dashboard')
    
    # Obtener las sesiones ordenadas por número
    sesiones = SeguimientoSesion.objects.filter(
        tratamiento=tratamiento
    ).order_by('numero_sesion')
    
    context = {
        'tratamiento': tratamiento,
        'sesiones': sesiones,
        'es_medico': es_medico_asignado,
        'es_paciente': es_paciente_asignado,
    }
    
    return render(request, 'medico/detalle_seguimiento.html', context)

@login_required
def programar_cita_sesion(request, sesion_id):
    """Vista para programar una cita para una sesión de seguimiento"""
    # Verificar que el usuario tenga el rol correcto (médico o admisión)
    if not request.user.rol or request.user.rol.nombre not in ['Medico', 'Admision']:
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener la sesión
    sesion = get_object_or_404(SeguimientoSesion, id=sesion_id)
    
    # Verificar que la sesión esté pendiente
    if sesion.estado != 'pendiente':
        messages.error(request, 'Esta sesión ya tiene una cita programada o ha sido completada')
        return redirect('detalle_seguimiento', tratamiento_id=sesion.tratamiento.id)
    
    # Si es POST, procesar el formulario
    if request.method == 'POST':
        fecha = request.POST.get('fecha')
        hora_inicio = request.POST.get('hora_inicio')
        consultorio_id = request.POST.get('consultorio')
        
        # Validar datos
        if not (fecha and hora_inicio and consultorio_id):
            messages.error(request, 'Todos los campos son obligatorios')
            return redirect('programar_cita_sesion', sesion_id=sesion.id)
        
        try:
            # Convertir fecha y hora
            fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
            hora_inicio_obj = datetime.strptime(hora_inicio, '%H:%M').time()
            # Calcular hora fin (1 hora después)
            hora_fin_obj = (datetime.combine(datetime.today(), hora_inicio_obj) + timedelta(hours=1)).time()
            
            # Obtener consultorio
            consultorio = get_object_or_404(Consultorio, id=consultorio_id)
            
            # Crear la cita
            cita = Cita.objects.create(
                paciente=sesion.tratamiento.paciente,
                medico=sesion.tratamiento.medico,
                consultorio=consultorio,
                fecha=fecha_obj,
                hora_inicio=hora_inicio_obj,
                hora_fin=hora_fin_obj,
                estado='pendiente',
                motivo=f"Sesión {sesion.numero_sesion} de tratamiento",
                tratamiento=sesion.tratamiento,
                reservado_por=request.user
            )
            
            # Actualizar la sesión
            sesion.cita = cita
            sesion.estado = 'programada'
            sesion.save()
            
            # Crear notificación para el paciente
            Notificacion.objects.create(
                usuario=sesion.tratamiento.paciente.usuario,
                mensaje=f"Se ha programado la cita para la sesión {sesion.numero_sesion} de su tratamiento.",
                tipo='confirmacion',
                importante=True,
                url_redireccion=f'/mis-tratamientos/{sesion.tratamiento.id}/',
                objeto_relacionado='tratamiento',
                objeto_id=sesion.tratamiento.id
            )
            
            messages.success(request, 'Cita programada exitosamente')
            return redirect('detalle_seguimiento', tratamiento_id=sesion.tratamiento.id)
            
        except Exception as e:
            messages.error(request, f'Error al programar la cita: {str(e)}')
            return redirect('programar_cita_sesion', sesion_id=sesion.id)
    
    # Obtener consultorios disponibles
    consultorios = Consultorio.objects.all()
    
    context = {
        'sesion': sesion,
        'consultorios': consultorios,
        'fecha_sugerida': sesion.fecha_programada,
    }
    
    return render(request, 'medico/programar_cita_sesion.html', context)

@login_required
def registrar_evolucion(request, sesion_id):
    """Vista para registrar la evolución de una sesión de seguimiento"""
    # Verificar que el usuario tenga el rol correcto (médico)
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener la sesión
    sesion = get_object_or_404(SeguimientoSesion, id=sesion_id)
    
    # Verificar que la sesión tenga una cita asociada y que el médico sea el asignado
    if not sesion.cita:
        messages.error(request, 'Esta sesión no tiene una cita programada')
        return redirect('detalle_seguimiento', tratamiento_id=sesion.tratamiento.id)
    
    if request.user.medico != sesion.tratamiento.medico:
        messages.error(request, 'No eres el médico asignado a este tratamiento')
        return redirect('dashboard')
    
    # Si es POST, procesar el formulario
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '')
        evolucion = request.POST.get('evolucion', '')
        
        if not evolucion:
            messages.error(request, 'El campo de evolución es obligatorio')
            return redirect('registrar_evolucion', sesion_id=sesion.id)
        
        # Marcar la sesión como completada
        sesion.marcar_completada(observaciones=observaciones, evolucion=evolucion)
        
        # Marcar la cita como atendida si no lo está
        if sesion.cita.estado != 'atendida':
            sesion.cita.estado = 'atendida'
            sesion.cita.save()
        
        messages.success(request, 'Evolución registrada exitosamente')
        return redirect('detalle_seguimiento', tratamiento_id=sesion.tratamiento.id)
    
    context = {
        'sesion': sesion,
        'tratamiento': sesion.tratamiento,
    }
    
    return render(request, 'medico/registrar_evolucion.html', context)

@login_required
def mis_tratamientos(request):
    """Vista para que los pacientes vean sus tratamientos"""
    # Verificar que el usuario tenga el rol correcto (paciente)
    if not request.user.rol or request.user.rol.nombre != 'Paciente':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener el paciente asociado al usuario
    try:
        paciente = request.user.paciente
    except Paciente.DoesNotExist:
        messages.error(request, 'No se encontró el perfil de paciente')
        return redirect('dashboard')
    
    # Obtener tratamientos activos y completados
    tratamientos_activos = TratamientoProgramado.objects.filter(
        paciente=paciente,
        estado='activo'
    ).order_by('-created_at')
    
    tratamientos_completados = TratamientoProgramado.objects.filter(
        paciente=paciente,
        estado='terminado'
    ).order_by('-created_at')
    
    tratamientos_cancelados = TratamientoProgramado.objects.filter(
        paciente=paciente,
        estado='cancelado'
    ).order_by('-created_at')
    
    context = {
        'tratamientos_activos': tratamientos_activos,
        'tratamientos_completados': tratamientos_completados,
        'tratamientos_cancelados': tratamientos_cancelados,
    }
    
    return render(request, 'paciente/mis_tratamientos.html', context)

@login_required
def cancelar_tratamiento(request, tratamiento_id):
    """Vista para cancelar un tratamiento"""
    # Verificar que el usuario tenga el rol correcto (médico)
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener el tratamiento
    tratamiento = get_object_or_404(TratamientoProgramado, id=tratamiento_id)
    
    # Verificar que el médico sea el asignado
    if request.user.medico != tratamiento.medico:
        messages.error(request, 'No eres el médico asignado a este tratamiento')
        return redirect('dashboard')
    
    # Si es POST, procesar la cancelación
    if request.method == 'POST':
        motivo = request.POST.get('motivo', '')
        
        if not motivo:
            messages.error(request, 'Debe proporcionar un motivo para la cancelación')
            return redirect('detalle_seguimiento', tratamiento_id=tratamiento.id)
        
        # Actualizar el tratamiento
        tratamiento.estado = 'cancelado'
        tratamiento.notas_seguimiento += f"\n\nCancelado el {timezone.now().strftime('%d/%m/%Y')} por: {motivo}"
        tratamiento.save()
        
        # Actualizar sesiones pendientes
        sesiones_pendientes = SeguimientoSesion.objects.filter(
            tratamiento=tratamiento,
            estado__in=['pendiente', 'programada']
        )
        
        for sesion in sesiones_pendientes:
            sesion.estado = 'cancelada'
            sesion.observaciones = f"Cancelada debido a cancelación del tratamiento: {motivo}"
            sesion.save()
            
            # Si hay cita asociada, cancelarla
            if sesion.cita and sesion.cita.estado in ['pendiente', 'confirmada']:
                sesion.cita.estado = 'cancelada'
                sesion.cita.save()
        
        # Crear notificación para el paciente
        Notificacion.objects.create(
            usuario=tratamiento.paciente.usuario,
            mensaje=f"Su tratamiento ha sido cancelado. Motivo: {motivo}",
            tipo='cancelacion',
            importante=True,
            url_redireccion='/mis-tratamientos/',
            objeto_relacionado='tratamiento',
            objeto_id=tratamiento.id
        )
        
        messages.success(request, 'Tratamiento cancelado exitosamente')
        return redirect('ver_seguimientos')
    
    context = {
        'tratamiento': tratamiento,
    }
    
    return render(request, 'medico/cancelar_tratamiento.html', context)

# API para obtener datos de seguimiento
@login_required
def api_sesiones_pendientes(request):
    """API para obtener sesiones pendientes de programación"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre not in ['Medico', 'Admision']:
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    # Filtrar por médico si es médico quien consulta
    if request.user.rol.nombre == 'Medico':
        try:
            medico = request.user.medico
            sesiones = SeguimientoSesion.objects.filter(
                tratamiento__medico=medico,
                estado='pendiente'
            )
        except Medico.DoesNotExist:
            return JsonResponse({'error': 'Perfil de médico no encontrado'}, status=404)
    else:
        # Para admisión, mostrar todas las sesiones pendientes
        sesiones = SeguimientoSesion.objects.filter(estado='pendiente')
    
    # Ordenar por fecha programada
    sesiones = sesiones.order_by('fecha_programada')
    
    # Convertir a JSON
    data = []
    for sesion in sesiones:
        data.append({
            'id': sesion.id,
            'tratamiento_id': sesion.tratamiento.id,
            'paciente': f"{sesion.tratamiento.paciente.usuario.nombres} {sesion.tratamiento.paciente.usuario.apellidos}",
            'medico': f"{sesion.tratamiento.medico.usuario.nombres} {sesion.tratamiento.medico.usuario.apellidos}",
            'numero_sesion': sesion.numero_sesion,
            'fecha_programada': sesion.fecha_programada.strftime('%d/%m/%Y'),
            'diagnostico': sesion.tratamiento.diagnostico[:50] + '...' if len(sesion.tratamiento.diagnostico) > 50 else sesion.tratamiento.diagnostico,
        })
    
    return JsonResponse({'sesiones': data})

@login_required
def api_buscar_medicamentos_prescripcion(request):
    """API para buscar medicamentos disponibles para prescripción"""
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    termino = request.GET.get('q', '')
    forma = request.GET.get('forma', '')
    
    if len(termino) < 2:
        return JsonResponse({'medicamentos': []})
    
    from .models import Medicamento
    
    # Filtrar medicamentos activos con stock
    medicamentos = Medicamento.objects.filter(
        activo=True,
        stock_actual__gt=0
    )
    
    # Aplicar filtro de búsqueda
    medicamentos = medicamentos.filter(
        Q(nombre_comercial__icontains=termino) |
        Q(nombre_generico__icontains=termino) |
        Q(codigo__icontains=termino) |
        Q(laboratorio__icontains=termino)
    )
    
    # Aplicar filtro de forma farmacéutica si se especifica
    if forma:
        medicamentos = medicamentos.filter(forma_farmaceutica__icontains=forma)
    
    # Limitar resultados
    medicamentos = medicamentos.order_by('nombre_comercial')[:20]
    
    # Convertir a JSON
    data = []
    for med in medicamentos:
        # Determinar estado del stock
        stock_estado = 'normal'
        if med.stock_actual <= med.stock_minimo:
            stock_estado = 'critico'
        elif med.stock_actual <= med.stock_minimo * 2:
            stock_estado = 'bajo'
        
        data.append({
            'id': med.id,
            'codigo': med.codigo,
            'nombre_comercial': med.nombre_comercial,
            'nombre_generico': med.nombre_generico,
            'concentracion': med.concentracion,
            'forma_farmaceutica': med.forma_farmaceutica,
            'laboratorio': med.laboratorio,
            'stock_actual': med.stock_actual,
            'stock_minimo': med.stock_minimo,
            'precio_unitario': float(med.precio_unitario),
            'stock_estado': stock_estado,
            'controlado': med.controlado,
            'fecha_vencimiento': med.fecha_vencimiento.strftime('%d/%m/%Y') if med.fecha_vencimiento else None
        })
    
    return JsonResponse({'medicamentos': data})

@login_required
def atender_sesion_seguimiento(request, sesion_id):
    """Vista especializada para atender sesiones de seguimiento con integración farmacológica"""
    # Verificar que el usuario tenga el rol correcto (médico)
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Obtener la sesión
    sesion = get_object_or_404(SeguimientoSesion, id=sesion_id)
    
    # Verificar que el médico sea el asignado al tratamiento
    if request.user.medico != sesion.tratamiento.medico:
        messages.error(request, 'No eres el médico asignado a este tratamiento')
        return redirect('dashboard')
    
    # Verificar que la sesión tenga una cita asociada
    if not sesion.cita:
        messages.error(request, 'Esta sesión no tiene una cita programada')
        return redirect('detalle_seguimiento', tratamiento_id=sesion.tratamiento.id)
    
    # Verificar que la cita esté en estado válido para atención
    if sesion.cita.estado not in ['pendiente', 'confirmada']:
        messages.error(request, 'Esta cita no está en estado válido para atención')
        return redirect('detalle_seguimiento', tratamiento_id=sesion.tratamiento.id)
    
    # Si es POST, procesar el formulario de atención
    if request.method == 'POST':
        observaciones = request.POST.get('observaciones', '')
        evolucion = request.POST.get('evolucion', '')
        
        # Campos farmacológicos
        sintomas_actuales = request.POST.get('sintomas_actuales', '')
        mejoria_observada = request.POST.get('mejoria_observada', '')
        requiere_ajuste_medicamentos = request.POST.get('requiere_ajuste_medicamentos') == 'on'
        observaciones_farmacologicas = request.POST.get('observaciones_farmacologicas', '')
        proxima_sesion_recomendada = request.POST.get('proxima_sesion_recomendada', 'on') == 'on'
        observaciones_proxima_sesion = request.POST.get('observaciones_proxima_sesion', '')
        
        # Prescripción de medicamentos
        prescribir_medicamentos = request.POST.get('prescribir_medicamentos') == 'on'
        
        if not evolucion:
            messages.error(request, 'El campo de evolución es obligatorio')
            return redirect('atender_sesion_seguimiento', sesion_id=sesion.id)
        
        # Actualizar los nuevos campos de la sesión
        sesion.sintomas_actuales = sintomas_actuales
        sesion.mejoria_observada = mejoria_observada
        sesion.requiere_ajuste_medicamentos = requiere_ajuste_medicamentos
        sesion.observaciones_farmacologicas = observaciones_farmacologicas
        sesion.proxima_sesion_recomendada = proxima_sesion_recomendada
        sesion.observaciones_proxima_sesion = observaciones_proxima_sesion
        
        # Crear receta si se prescribieron medicamentos
        receta_creada = None
        if prescribir_medicamentos:
            from .models import RecetaMedica
            
            # Procesar medicamentos seleccionados
            medicamentos_ids = request.POST.getlist('medicamentos')
            
            # Solo crear receta si hay medicamentos seleccionados
            if medicamentos_ids:
                receta_creada = RecetaMedica.objects.create(
                    sesion_seguimiento=sesion,
                    paciente=sesion.tratamiento.paciente,
                    medico=sesion.tratamiento.medico,
                    observaciones_medico=observaciones_farmacologicas if observaciones_farmacologicas else "Medicamentos prescritos en sesión de seguimiento",
                    urgente=False  # Se puede ajustar según necesidad
                )
                sesion.receta_seguimiento = receta_creada
                
                # Procesar cada medicamento
                for med_id in medicamentos_ids:
                    if med_id:
                        from .models import Medicamento, DetalleReceta
                        try:
                            medicamento = Medicamento.objects.get(id=med_id)
                            cantidad = request.POST.get(f'cantidad_{med_id}', 1)
                            dosis = request.POST.get(f'dosis_{med_id}', '')
                            frecuencia = request.POST.get(f'frecuencia_{med_id}', '')
                            duracion = request.POST.get(f'duracion_{med_id}', 7)
                            instrucciones = request.POST.get(f'instrucciones_{med_id}', '')
                            
                            if dosis and frecuencia and instrucciones:
                                DetalleReceta.objects.create(
                                    receta=receta_creada,
                                    medicamento=medicamento,
                                    cantidad_prescrita=int(cantidad),
                                    dosis=dosis,
                                    frecuencia=frecuencia,
                                    duracion_dias=int(duracion),
                                    instrucciones=instrucciones
                                )
                        except (Medicamento.DoesNotExist, ValueError):
                            continue
        
        # Marcar la sesión como completada
        sesion.marcar_completada(observaciones=observaciones, evolucion=evolucion)
        
        # Marcar la cita como atendida
        sesion.cita.estado = 'atendida'
        sesion.cita.save()
        
        # Mensajes de éxito
        if receta_creada:
            messages.success(request, f'Sesión de seguimiento atendida exitosamente. Receta {receta_creada.codigo_receta} generada.')
        else:
            messages.success(request, 'Sesión de seguimiento atendida exitosamente')
        
        return redirect('detalle_seguimiento', tratamiento_id=sesion.tratamiento.id)
    
    # Obtener evoluciones anteriores del tratamiento
    evoluciones_anteriores = SeguimientoSesion.objects.filter(
        tratamiento=sesion.tratamiento,
        estado='completada',
        numero_sesion__lt=sesion.numero_sesion
    ).order_by('-numero_sesion')[:3]  # Últimas 3 evoluciones
    
    # Obtener medicamentos disponibles para prescripción
    from .models import Medicamento
    medicamentos_disponibles = Medicamento.objects.filter(
        activo=True,
        stock_actual__gt=0
    ).order_by('nombre_comercial')
    
    # Obtener recetas anteriores del paciente
    recetas_anteriores = []
    if sesion.tratamiento.paciente:
        from .models import RecetaMedica
        recetas_anteriores = RecetaMedica.objects.filter(
            paciente=sesion.tratamiento.paciente,
            estado='dispensada'
        ).order_by('-fecha_dispensacion')[:3]
    
    context = {
        'sesion': sesion,
        'tratamiento': sesion.tratamiento,
        'cita': sesion.cita,
        'evoluciones_anteriores': evoluciones_anteriores,
        'paciente': sesion.tratamiento.paciente,
        'medico': sesion.tratamiento.medico,
        'medicamentos_disponibles': medicamentos_disponibles,
        'recetas_anteriores': recetas_anteriores,
    }
    
    return render(request, 'medico/atender_sesion_seguimiento.html', context)
