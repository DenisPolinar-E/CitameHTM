# ---- Funciones adicionales para Análisis Temporal ----
@login_required
def comparativas(request):
    """
    Vista para mostrar comparativas de citas entre diferentes períodos.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Comparativas de Citas',
        'subtitulo': 'Análisis Temporal'
    }
    
    return render(request, 'admin/comparativas.html', context)


@login_required
def tendencias(request):
    """
    Vista para mostrar tendencias en la programación de citas a lo largo del tiempo.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Tendencias de Citas',
        'subtitulo': 'Análisis Temporal'
    }
    
    return render(request, 'admin/tendencias.html', context)


@login_required
def tasas_asistencia(request):
    """
    Vista para mostrar las tasas de asistencia a citas programadas.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Tasas de Asistencia',
        'subtitulo': 'Análisis Temporal'
    }
    
    return render(request, 'admin/tasas_asistencia.html', context)


# ---- Funciones para Análisis por Origen ----
@login_required
def citas_admision(request):
    """
    Vista para mostrar análisis de citas creadas por admisión.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas por Admisión',
        'subtitulo': 'Análisis por Origen'
    }
    
    return render(request, 'admin/citas_admision.html', context)


@login_required
def citas_derivacion(request):
    """
    Vista para mostrar análisis de citas creadas por derivación médica.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas por Derivación',
        'subtitulo': 'Análisis por Origen'
    }
    
    return render(request, 'admin/citas_derivacion.html', context)


@login_required
def citas_seguimiento(request):
    """
    Vista para mostrar análisis de citas creadas para seguimiento de tratamientos.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas de Seguimiento',
        'subtitulo': 'Análisis por Origen'
    }
    
    return render(request, 'admin/citas_seguimiento.html', context)


# ---- Funciones para Análisis por Especialidad y Médico ----
@login_required
def analisis_especialidad(request):
    """
    Vista para mostrar análisis de citas por especialidad médica.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Análisis por Especialidad',
        'subtitulo': 'Distribución de Citas'
    }
    
    return render(request, 'admin/analisis_especialidad.html', context)


@login_required
def analisis_medico(request):
    """
    Vista para mostrar análisis de citas por médico.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Análisis por Médico',
        'subtitulo': 'Distribución de Citas'
    }
    
    return render(request, 'admin/analisis_medico.html', context)


# ---- Funciones para Análisis de Estado ----
@login_required
def citas_completadas(request):
    """
    Vista para mostrar análisis de citas completadas (atendidas).
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas Completadas',
        'subtitulo': 'Análisis de Estado'
    }
    
    return render(request, 'admin/citas_completadas.html', context)


@login_required
def citas_canceladas(request):
    """
    Vista para mostrar análisis de citas canceladas.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Citas Canceladas',
        'subtitulo': 'Análisis de Estado'
    }
    
    return render(request, 'admin/citas_canceladas.html', context)


@login_required
def citas_inasistencias(request):
    """
    Vista para mostrar análisis de inasistencias a citas.
    """
    # Obtener especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Obtener todos los médicos para el filtro
    medicos = Medico.objects.all().select_related('usuario', 'especialidad')
    
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'especialidades': especialidades,
        'medicos': medicos,
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Inasistencias',
        'subtitulo': 'Análisis de Estado'
    }
    
    return render(request, 'admin/citas_inasistencias.html', context)


# ---- Funciones para Reportes Especiales ----
@login_required
def reporte_pacientes(request):
    """
    Vista para mostrar reportes especiales sobre pacientes (frecuentes y nuevos).
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Reporte de Pacientes',
        'subtitulo': 'Reportes Especiales'
    }
    
    return render(request, 'admin/reporte_pacientes.html', context)


@login_required
def reporte_satisfaccion(request):
    """
    Vista para mostrar reportes de satisfacción de pacientes.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Satisfacción de Pacientes',
        'subtitulo': 'Reportes Especiales'
    }
    
    return render(request, 'admin/reporte_satisfaccion.html', context)


@login_required
def indicadores_clave(request):
    """
    Vista para mostrar indicadores clave de rendimiento del hospital.
    """
    # Configurar fechas predeterminadas (último mes)
    fecha_fin = timezone.now().date()
    fecha_inicio = fecha_fin - timedelta(days=30)
    
    context = {
        'fecha_inicio': fecha_inicio.strftime('%Y-%m-%d'),
        'fecha_fin': fecha_fin.strftime('%Y-%m-%d'),
        'titulo': 'Indicadores Clave',
        'subtitulo': 'Reportes Especiales'
    }
    
    return render(request, 'admin/indicadores_clave.html', context)
