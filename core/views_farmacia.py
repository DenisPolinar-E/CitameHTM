from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.db.models import Q, Count, Sum, F
from django.utils import timezone
from django.core.paginator import Paginator
from datetime import datetime, timedelta
from .models import (
    RecetaMedica, DetalleReceta, Medicamento, MovimientoInventario,
    Paciente, Medico, Usuario, Rol
)
from .utils_notificaciones import crear_notificacion

@login_required
def dashboard_farmacia(request):
    """Dashboard principal de farmacia"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Estadísticas generales
    recetas_pendientes = RecetaMedica.objects.filter(estado='pendiente').count()
    recetas_dispensadas_hoy = RecetaMedica.objects.filter(
        estado='dispensada',
        fecha_dispensacion__date=timezone.now().date()
    ).count()
    
    medicamentos_stock_critico = Medicamento.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).count()
    
    medicamentos_proximos_vencer = Medicamento.objects.filter(
        activo=True,
        fecha_vencimiento__lte=timezone.now().date() + timedelta(days=30)
    ).count()
    
    # Recetas pendientes recientes
    recetas_recientes = RecetaMedica.objects.filter(
        estado='pendiente'
    ).select_related(
        'paciente__usuario', 'medico__usuario'
    ).order_by('-fecha_prescripcion')[:5]
    
    # Medicamentos más solicitados (últimos 30 días)
    medicamentos_populares = DetalleReceta.objects.filter(
        receta__fecha_prescripcion__gte=timezone.now() - timedelta(days=30)
    ).values(
        'medicamento__nombre_comercial', 'medicamento__nombre_generico'
    ).annotate(
        total_prescrito=Sum('cantidad_prescrita')
    ).order_by('-total_prescrito')[:5]
    
    context = {
        'recetas_pendientes': recetas_pendientes,
        'recetas_dispensadas_hoy': recetas_dispensadas_hoy,
        'medicamentos_stock_critico': medicamentos_stock_critico,
        'medicamentos_proximos_vencer': medicamentos_proximos_vencer,
        'recetas_recientes': recetas_recientes,
        'medicamentos_populares': medicamentos_populares,
    }
    
    return render(request, 'farmacia/dashboard.html', context)

@login_required
def recetas_pendientes(request):
    """Lista de recetas pendientes por dispensar"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Filtros
    busqueda = request.GET.get('busqueda', '')
    estado_filtro = request.GET.get('estado', 'pendiente')
    urgente_filtro = request.GET.get('urgente', '')
    
    # Query base
    recetas = RecetaMedica.objects.select_related(
        'paciente__usuario', 'medico__usuario'
    ).prefetch_related('detalles__medicamento')
    
    # Aplicar filtros
    if estado_filtro:
        recetas = recetas.filter(estado=estado_filtro)
    
    if urgente_filtro == 'si':
        recetas = recetas.filter(urgente=True)
    
    if busqueda:
        recetas = recetas.filter(
            Q(codigo_receta__icontains=busqueda) |
            Q(paciente__usuario__nombres__icontains=busqueda) |
            Q(paciente__usuario__apellidos__icontains=busqueda) |
            Q(paciente__usuario__dni__icontains=busqueda)
        )
    
    # Ordenar por urgente primero, luego por fecha
    recetas = recetas.order_by('-urgente', '-fecha_prescripcion')
    
    context = {
        'recetas': recetas,
        'busqueda': busqueda,
        'estado_filtro': estado_filtro,
        'urgente_filtro': urgente_filtro,
    }
    
    return render(request, 'farmacia/recetas_pendientes.html', context)

@login_required
def detalle_receta(request, receta_id):
    """Detalle de una receta específica"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    receta = get_object_or_404(
        RecetaMedica.objects.select_related(
            'paciente__usuario', 'medico__usuario'
        ).prefetch_related('detalles__medicamento'),
        id=receta_id
    )
    
    context = {
        'receta': receta,
    }
    
    return render(request, 'farmacia/detalle_receta.html', context)

@login_required
def dispensar_receta(request, receta_id):
    """Dispensar medicamentos de una receta"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    receta = get_object_or_404(RecetaMedica, id=receta_id)
    
    # Verificar que la receta puede ser dispensada
    if not receta.puede_dispensarse():
        messages.error(request, 'Esta receta no puede ser dispensada (ya dispensada o vencida)')
        return redirect('detalle_receta', receta_id=receta.id)
    
    if request.method == 'POST':
        # Procesar dispensación
        detalles = receta.detalles.all()
        errores = []
        
        for detalle in detalles:
            cantidad_a_dispensar = int(request.POST.get(f'cantidad_{detalle.id}', 0))
            lote = request.POST.get(f'lote_{detalle.id}', '')
            
            if cantidad_a_dispensar > 0:
                if cantidad_a_dispensar > detalle.medicamento.stock_actual:
                    errores.append(f"No hay suficiente stock de {detalle.medicamento.nombre_comercial}")
                elif cantidad_a_dispensar > detalle.cantidad_prescrita:
                    errores.append(f"No puede dispensar más de lo prescrito para {detalle.medicamento.nombre_comercial}")
                else:
                    # Dispensar medicamento
                    detalle.dispensar(cantidad_a_dispensar, lote)
        
        if errores:
            for error in errores:
                messages.error(request, error)
        else:
            # Verificar si la receta está completamente dispensada
            if receta.total_dispensado():
                receta.marcar_dispensada(request.user)
                
                # Crear notificación para el paciente
                crear_notificacion(
                    usuario=receta.paciente.usuario,
                    mensaje=f"Su receta {receta.codigo_receta} ha sido dispensada y está lista para recoger.",
                    tipo='informacion',
                    importante=True
                )
                
                messages.success(request, f'Receta {receta.codigo_receta} dispensada completamente')
            else:
                receta.estado = 'parcial'
                receta.save()
                messages.success(request, 'Medicamentos dispensados parcialmente')
            
            return redirect('recetas_pendientes')
    
    context = {
        'receta': receta,
    }
    
    return render(request, 'farmacia/dispensar_receta.html', context)

@login_required
def inventario_medicamentos(request):
    """Gestión de inventario de medicamentos"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Filtros
    busqueda = request.GET.get('busqueda', '')
    estado_stock = request.GET.get('stock', '')  # critico, bajo, normal
    forma_farmaceutica = request.GET.get('forma', '')
    
    # Query base
    medicamentos = Medicamento.objects.filter(activo=True)
    
    # Aplicar filtros
    if busqueda:
        medicamentos = medicamentos.filter(
            Q(nombre_comercial__icontains=busqueda) |
            Q(nombre_generico__icontains=busqueda) |
            Q(codigo__icontains=busqueda)
        )
    
    if forma_farmaceutica:
        medicamentos = medicamentos.filter(forma_farmaceutica=forma_farmaceutica)
    
    if estado_stock == 'critico':
        medicamentos = medicamentos.filter(stock_actual__lte=F('stock_minimo'))
    elif estado_stock == 'bajo':
        medicamentos = medicamentos.filter(
            stock_actual__gt=F('stock_minimo'),
            stock_actual__lte=F('stock_minimo') * 2
        )
    elif estado_stock == 'normal':
        medicamentos = medicamentos.filter(stock_actual__gt=F('stock_minimo') * 2)
    
    # Ordenar
    medicamentos = medicamentos.order_by('nombre_comercial')
    
    # Paginación - 20 medicamentos por página
    paginator = Paginator(medicamentos, 20)
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)
    
    # Obtener formas farmacéuticas para el filtro
    formas_disponibles = Medicamento.objects.filter(
        activo=True
    ).values_list('forma_farmaceutica', flat=True).distinct()
    
    context = {
        'medicamentos': page_obj,
        'busqueda': busqueda,
        'estado_stock': estado_stock,
        'forma_farmaceutica': forma_farmaceutica,
        'formas_disponibles': formas_disponibles,
        'page_obj': page_obj,
        'paginator': paginator,
    }
    
    return render(request, 'farmacia/inventario.html', context)

@login_required
def alertas_farmacia(request):
    """Vista de alertas de farmacia (stock crítico, medicamentos por vencer)"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Medicamentos con stock crítico
    stock_critico = Medicamento.objects.filter(
        activo=True,
        stock_actual__lte=F('stock_minimo')
    ).order_by('stock_actual')
    
    # Medicamentos próximos a vencer (30 días)
    proximos_vencer = Medicamento.objects.filter(
        activo=True,
        fecha_vencimiento__lte=timezone.now().date() + timedelta(days=30)
    ).order_by('fecha_vencimiento')
    
    # Medicamentos ya vencidos
    vencidos = Medicamento.objects.filter(
        activo=True,
        fecha_vencimiento__lt=timezone.now().date()
    ).order_by('fecha_vencimiento')
    
    context = {
        'stock_critico': stock_critico,
        'proximos_vencer': proximos_vencer,
        'vencidos': vencidos,
    }
    
    return render(request, 'farmacia/alertas.html', context)

# === APIs para farmacia ===

@login_required
def api_buscar_medicamento(request):
    """API para buscar medicamentos disponibles"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    termino = request.GET.get('q', '')
    if len(termino) < 2:
        return JsonResponse({'medicamentos': []})
    
    medicamentos = Medicamento.objects.filter(
        activo=True,
        stock_actual__gt=0
    ).filter(
        Q(nombre_comercial__icontains=termino) |
        Q(nombre_generico__icontains=termino) |
        Q(codigo__icontains=termino)
    )[:10]
    
    data = []
    for med in medicamentos:
        data.append({
            'id': med.id,
            'codigo': med.codigo,
            'nombre_comercial': med.nombre_comercial,
            'nombre_generico': med.nombre_generico,
            'concentracion': med.concentracion,
            'forma_farmaceutica': med.forma_farmaceutica,
            'stock_actual': med.stock_actual,
            'precio_unitario': float(med.precio_unitario),
        })
    
    return JsonResponse({'medicamentos': data})

@login_required
def api_estadisticas_farmacia(request):
    """API para obtener estadísticas de farmacia"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    # Estadísticas de los últimos 7 días
    hoy = timezone.now().date()
    hace_7_dias = hoy - timedelta(days=7)
    
    dispensaciones_por_dia = []
    for i in range(7):
        fecha = hoy - timedelta(days=i)
        dispensaciones = RecetaMedica.objects.filter(
            estado='dispensada',
            fecha_dispensacion__date=fecha
        ).count()
        dispensaciones_por_dia.append({
            'fecha': fecha.strftime('%d/%m'),
            'dispensaciones': dispensaciones
        })
    
    # Medicamentos más dispensados
    medicamentos_top = DetalleReceta.objects.filter(
        fecha_dispensacion__gte=hace_7_dias
    ).values(
        'medicamento__nombre_comercial'
    ).annotate(
        total=Sum('cantidad_dispensada')
    ).order_by('-total')[:5]
    
    data = {
        'dispensaciones_por_dia': list(reversed(dispensaciones_por_dia)),
        'medicamentos_top': list(medicamentos_top),
    }
    
    return JsonResponse(data)

# === GESTIÓN AVANZADA DE INVENTARIO ===

@login_required
def entrada_medicamentos(request):
    """Vista para registrar entrada de medicamentos al inventario"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    if request.method == 'POST':
        medicamento_id = request.POST.get('medicamento_id')
        cantidad = int(request.POST.get('cantidad', 0))
        lote = request.POST.get('lote', '')
        proveedor = request.POST.get('proveedor', '')
        precio_unitario = request.POST.get('precio_unitario', 0)
        numero_factura = request.POST.get('numero_factura', '')
        fecha_vencimiento = request.POST.get('fecha_vencimiento')
        motivo = request.POST.get('motivo', 'Compra de medicamentos')
        
        try:
            medicamento = Medicamento.objects.get(id=medicamento_id)
            stock_anterior = medicamento.stock_actual
            
            # Actualizar stock
            medicamento.stock_actual += cantidad
            if precio_unitario:
                medicamento.precio_unitario = precio_unitario
            if fecha_vencimiento:
                medicamento.fecha_vencimiento = fecha_vencimiento
            medicamento.save()
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                medicamento=medicamento,
                tipo_movimiento='entrada',
                cantidad=cantidad,
                motivo=motivo,
                usuario=request.user,
                lote_referencia=lote,
                proveedor=proveedor,
                precio_unitario_momento=precio_unitario,
                stock_anterior=stock_anterior,
                stock_nuevo=medicamento.stock_actual,
                numero_factura=numero_factura
            )
            
            messages.success(request, f'Entrada registrada: +{cantidad} unidades de {medicamento.nombre_comercial}')
            return redirect('inventario_medicamentos')
            
        except Medicamento.DoesNotExist:
            messages.error(request, 'Medicamento no encontrado')
        except ValueError:
            messages.error(request, 'Datos inválidos')
    
    # Obtener medicamentos para el formulario
    medicamentos = Medicamento.objects.filter(activo=True).order_by('nombre_comercial')
    
    context = {
        'medicamentos': medicamentos,
    }
    
    return render(request, 'farmacia/entrada_medicamentos.html', context)

@login_required
def ajuste_inventario(request):
    """Vista para realizar ajustes de inventario (positivos o negativos)"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    if request.method == 'POST':
        medicamento_id = request.POST.get('medicamento_id')
        tipo_ajuste = request.POST.get('tipo_ajuste')  # 'positivo' o 'negativo'
        cantidad = int(request.POST.get('cantidad', 0))
        motivo = request.POST.get('motivo', '')
        
        try:
            medicamento = Medicamento.objects.get(id=medicamento_id)
            stock_anterior = medicamento.stock_actual
            
            if tipo_ajuste == 'positivo':
                medicamento.stock_actual += cantidad
                tipo_movimiento = 'ajuste_positivo'
            else:
                if cantidad > medicamento.stock_actual:
                    messages.error(request, 'No se puede ajustar más stock del disponible')
                    return redirect('ajuste_inventario')
                medicamento.stock_actual -= cantidad
                tipo_movimiento = 'ajuste_negativo'
            
            medicamento.save()
            
            # Registrar movimiento
            MovimientoInventario.objects.create(
                medicamento=medicamento,
                tipo_movimiento=tipo_movimiento,
                cantidad=cantidad,
                motivo=motivo,
                usuario=request.user,
                stock_anterior=stock_anterior,
                stock_nuevo=medicamento.stock_actual
            )
            
            signo = '+' if tipo_ajuste == 'positivo' else '-'
            messages.success(request, f'Ajuste registrado: {signo}{cantidad} unidades de {medicamento.nombre_comercial}')
            return redirect('inventario_medicamentos')
            
        except Medicamento.DoesNotExist:
            messages.error(request, 'Medicamento no encontrado')
        except ValueError:
            messages.error(request, 'Datos inválidos')
    
    # Obtener medicamentos para el formulario
    medicamentos = Medicamento.objects.filter(activo=True).order_by('nombre_comercial')
    
    context = {
        'medicamentos': medicamentos,
    }
    
    return render(request, 'farmacia/ajuste_inventario.html', context)

@login_required
def historial_movimientos(request):
    """Vista para ver el historial de movimientos de inventario"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Filtros
    medicamento_id = request.GET.get('medicamento')
    tipo_movimiento = request.GET.get('tipo')
    fecha_desde = request.GET.get('fecha_desde')
    fecha_hasta = request.GET.get('fecha_hasta')
    
    # Query base
    movimientos = MovimientoInventario.objects.select_related(
        'medicamento', 'usuario'
    ).all()
    
    # Aplicar filtros
    if medicamento_id:
        movimientos = movimientos.filter(medicamento_id=medicamento_id)
    
    if tipo_movimiento:
        movimientos = movimientos.filter(tipo_movimiento=tipo_movimiento)
    
    if fecha_desde:
        movimientos = movimientos.filter(fecha_movimiento__gte=fecha_desde)
    
    if fecha_hasta:
        fecha_hasta_obj = datetime.strptime(fecha_hasta, '%Y-%m-%d').replace(hour=23, minute=59, second=59)
        movimientos = movimientos.filter(fecha_movimiento__lte=fecha_hasta_obj)
    
    movimientos = movimientos.order_by('-fecha_movimiento')
    
    # Obtener medicamentos para filtro
    medicamentos = Medicamento.objects.filter(activo=True).order_by('nombre_comercial')
    
    # Estadísticas rápidas
    total_entradas = movimientos.filter(
        tipo_movimiento__in=['entrada', 'ajuste_positivo', 'devolucion']
    ).count()
    total_salidas = movimientos.filter(
        tipo_movimiento__in=['salida', 'ajuste_negativo', 'vencimiento', 'dañado']
    ).count()
    
    context = {
        'movimientos': movimientos,
        'medicamentos': medicamentos,
        'medicamento_id': medicamento_id,
        'tipo_movimiento': tipo_movimiento,
        'fecha_desde': fecha_desde,
        'fecha_hasta': fecha_hasta,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
    }
    
    return render(request, 'farmacia/historial_movimientos.html', context)

@login_required
def detalle_medicamento_inventario(request, medicamento_id):
    """Vista detallada de un medicamento específico en el inventario"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    medicamento = get_object_or_404(Medicamento, id=medicamento_id)
    
    # Movimientos recientes (últimos 20)
    movimientos_recientes = MovimientoInventario.objects.filter(
        medicamento=medicamento
    ).select_related('usuario').order_by('-fecha_movimiento')[:20]
    
    # Estadísticas del medicamento
    total_entradas = MovimientoInventario.objects.filter(
        medicamento=medicamento,
        tipo_movimiento__in=['entrada', 'ajuste_positivo', 'devolucion']
    ).aggregate(total=Sum('cantidad'))['total'] or 0
    
    total_salidas = MovimientoInventario.objects.filter(
        medicamento=medicamento,
        tipo_movimiento__in=['salida', 'ajuste_negativo', 'vencimiento', 'dañado']
    ).aggregate(total=Sum('cantidad'))['total'] or 0
    
    # Dispensaciones del último mes
    ultimo_mes = timezone.now() - timedelta(days=30)
    dispensaciones_mes = DetalleReceta.objects.filter(
        medicamento=medicamento,
        fecha_dispensacion__gte=ultimo_mes
    ).aggregate(total=Sum('cantidad_dispensada'))['total'] or 0
    
    # Promedio de dispensación diaria
    promedio_diario = dispensaciones_mes / 30 if dispensaciones_mes > 0 else 0
    
    # Días estimados de stock
    dias_stock_estimado = medicamento.stock_actual / promedio_diario if promedio_diario > 0 else float('inf')
    
    context = {
        'medicamento': medicamento,
        'movimientos_recientes': movimientos_recientes,
        'total_entradas': total_entradas,
        'total_salidas': total_salidas,
        'dispensaciones_mes': dispensaciones_mes,
        'promedio_diario': round(promedio_diario, 2),
        'dias_stock_estimado': round(dias_stock_estimado, 1) if dias_stock_estimado != float('inf') else 'Ilimitado',
    }
    
    return render(request, 'farmacia/detalle_medicamento.html', context)

@login_required
def reporte_inventario(request):
    """Vista para generar reportes de inventario"""
    if not request.user.rol or request.user.rol.nombre != 'Farmacéutico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('dashboard')
    
    # Estadísticas generales
    total_medicamentos = Medicamento.objects.filter(activo=True).count()
    valor_total_inventario = Medicamento.objects.filter(activo=True).aggregate(
        total=Sum(F('stock_actual') * F('precio_unitario'))
    )['total'] or 0
    
    # Medicamentos por estado de stock
    stock_critico = Medicamento.objects.filter(
        activo=True, stock_actual__lte=F('stock_minimo')
    ).count()
    
    stock_bajo = Medicamento.objects.filter(
        activo=True,
        stock_actual__gt=F('stock_minimo'),
        stock_actual__lte=F('stock_minimo') * 2
    ).count()
    
    stock_normal = total_medicamentos - stock_critico - stock_bajo
    
    # Medicamentos próximos a vencer
    proximos_vencer_30 = Medicamento.objects.filter(
        activo=True,
        fecha_vencimiento__lte=timezone.now().date() + timedelta(days=30)
    ).count()
    
    # Top 10 medicamentos más dispensados (último mes)
    ultimo_mes = timezone.now() - timedelta(days=30)
    top_dispensados = DetalleReceta.objects.filter(
        fecha_dispensacion__gte=ultimo_mes
    ).values(
        'medicamento__nombre_comercial',
        'medicamento__codigo'
    ).annotate(
        total_dispensado=Sum('cantidad_dispensada')
    ).order_by('-total_dispensado')[:10]
    
    # Movimientos del último mes por tipo
    movimientos_mes = MovimientoInventario.objects.filter(
        fecha_movimiento__gte=ultimo_mes
    ).values('tipo_movimiento').annotate(
        total=Sum('cantidad')
    ).order_by('-total')
    
    context = {
        'total_medicamentos': total_medicamentos,
        'valor_total_inventario': valor_total_inventario,
        'stock_critico': stock_critico,
        'stock_bajo': stock_bajo,
        'stock_normal': stock_normal,
        'proximos_vencer_30': proximos_vencer_30,
        'top_dispensados': top_dispensados,
        'movimientos_mes': movimientos_mes,
    }
    
    return render(request, 'farmacia/reporte_inventario.html', context) 