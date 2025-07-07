from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count, Sum
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from .forms import *
import json
from datetime import datetime, timedelta
from django.db.models import Sum
from core.models import DetalleReceta, Medicamento
from django.contrib.auth.models import Group

# Vistas pÃºblicas
def home(request):
    """Vista de la pÃ¡gina de bienvenida"""
    return render(request, 'home.html')

def login_view(request):
    """Vista de inicio de sesiÃ³n"""
    if request.method == 'POST':
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        user = authenticate(request, username=dni, password=password)
        
        if user is not None:
            login(request, user)
            
            # RedirecciÃ³n segÃºn el rol del usuario
            if user.rol:
                if user.rol.nombre == 'Paciente':
                    return redirect('dashboard_paciente')
                elif user.rol.nombre == 'Medico':
                    return redirect('dashboard_medico')
                elif user.rol.nombre == 'Admision':
                    return redirect('dashboard_admision')
                elif user.rol.nombre == 'Administrador':
                    return redirect('dashboard_admin')
                elif user.rol.nombre == 'Farmacéutico':
                    return redirect('dashboard_farmacia')
            
            # Si no tiene rol asignado, redirigir a la pÃ¡gina principal
            return redirect('home')
        else:
            messages.error(request, 'DNI o contraseÃ±a incorrectos')
    
    return render(request, 'auth/login.html')

def registro_view(request):
    """Vista de registro de usuarios con selecciÃ³n de rol"""
    # Cargar todas las especialidades para el formulario
    from .models import Especialidad
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    if request.method == 'POST':
        form = RegistroPacienteForm(request.POST)
        if form.is_valid():
            # Crear usuario
            user = form.save(commit=False)
            user.username = form.cleaned_data.get('dni')  # Usar DNI como nombre de usuario
            user.set_password(form.cleaned_data.get('password'))
            
            # Obtener el rol seleccionado
            rol_nombre = request.POST.get('rol')
            rol, created = Rol.objects.get_or_create(nombre=rol_nombre)
            user.rol = rol
            user.save()
            
            # Crear perfil segÃºn el rol
            if rol_nombre == 'Paciente':
                Paciente.objects.create(usuario=user)
            elif rol_nombre == 'Medico':
                # Para mÃ©dicos, usar la especialidad seleccionada o una por defecto
                from .models import Medico
                especialidad_id = request.POST.get('especialidad')
                
                try:
                    if especialidad_id and especialidad_id.isdigit():
                        especialidad = Especialidad.objects.get(id=especialidad_id)
                    else:
                        # Si no se seleccionÃ³ especialidad, usar General como predeterminada
                        especialidad, _ = Especialidad.objects.get_or_create(nombre='General')
                except Especialidad.DoesNotExist:
                    especialidad, _ = Especialidad.objects.get_or_create(nombre='General')
                
                # Asignar un CMP provisional que se actualizarÃ¡ despuÃ©s
                cmp_provisional = f"TEMP-{user.dni}"
                Medico.objects.create(usuario=user, especialidad=especialidad, cmp=cmp_provisional)
            
            # Iniciar sesiÃ³n automÃ¡ticamente
            login(request, user)
            messages.success(request, f'¡Registro exitoso como {rol_nombre}! Bienvenido al sistema.')
            
            # Redireccionar segÃºn el rol
            if rol_nombre == 'Paciente':
                return redirect('dashboard_paciente')
            elif rol_nombre == 'Medico':
                return redirect('dashboard_medico')
            elif rol_nombre == 'Admision':
                return redirect('dashboard_admision')
            elif rol_nombre == 'Administrador':
                return redirect('dashboard_admin')
            return redirect('dashboard')
    else:
        form = RegistroPacienteForm()
    
    return render(request, 'auth/registro.html', {
        'form': form,
        'especialidades': especialidades
    })

def logout_view(request):
    """Cerrar sesiÃ³n"""
    logout(request)
    return redirect('home')

# Vistas protegidas por rol
@login_required
def dashboard_view(request):
    """Redirecciona al dashboard especÃ­fico segÃºn el rol del usuario"""
    if request.user.rol:
        if request.user.rol.nombre == 'Paciente':
            return redirect('dashboard_paciente')
        elif request.user.rol.nombre == 'Medico':
            return redirect('dashboard_medico')
        elif request.user.rol.nombre == 'Admision':
            return redirect('dashboard_admision')
        elif request.user.rol.nombre == 'Administrador':
            return redirect('dashboard_admin')
        elif request.user.rol.nombre == 'Farmacéutico':
            return redirect('dashboard_farmacia')
    
    # Si no tiene rol asignado, mostrar mensaje y redirigir a home
    messages.warning(request, 'No tienes un rol asignado en el sistema.')
    return redirect('home')

# Dashboards por rol
@login_required
def dashboard_paciente(request):
    """Dashboard para pacientes"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Paciente':
        messages.error(request, 'No tienes permiso para acceder a esta pagina')
        return redirect('home')
    
    try:
        paciente = request.user.paciente
        
        # Obtener prÃ³ximas citas
        proximas_citas = Cita.objects.filter(
            paciente=paciente,
            fecha__gte=timezone.now().date(),
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora_inicio')[:5]
        
        # Obtener historial mÃ©dico
        historial = HistorialMedico.objects.filter(paciente=paciente).order_by('-fecha')[:5]
        
        # Obtener derivaciones activas
        derivaciones = Derivacion.objects.filter(
            paciente=paciente,
            estado='pendiente',
            fecha_derivacion__gte=timezone.now().date() - timedelta(days=30)
        )
        
        # Obtener notificaciones no leÃ­das
        notificaciones = Notificacion.objects.filter(
            usuario=request.user,
            leido=False
        ).order_by('-fecha_envio')[:5]
        
        context = {
            'proximas_citas': proximas_citas,
            'historial': historial,
            'derivaciones': derivaciones,
            'notificaciones': notificaciones,
        }
        
        return render(request, 'dashboard/paciente/dashboard.html', context)
    except Paciente.DoesNotExist:
        messages.error(request, 'No se encontro el perfil de paciente')
        return redirect('home')

@login_required
def dashboard_medico(request):
    """Dashboard para mÃ©dicos"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta pgina')
        return redirect('home')
    
    try:
        medico = request.user.medico
        
        # Obtener citas del dÃ­a
        hoy = timezone.now().date()
        citas_hoy = Cita.objects.filter(
            medico=medico,
            fecha=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('hora_inicio')
        
        # Obtener prÃ³ximas citas (excluyendo hoy)
        proximas_citas = Cita.objects.filter(
            medico=medico,
            fecha__gt=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora_inicio')[:10]
        
        # Obtener derivaciones realizadas recientemente
        derivaciones = Derivacion.objects.filter(
            medico_origen=medico
        ).order_by('-fecha_derivacion')[:5]
        
        # Obtener notificaciones no leÃ­das
        notificaciones = Notificacion.objects.filter(
            usuario=request.user,
            leido=False
        ).order_by('-fecha_envio')[:5]
        
        context = {
            'citas_hoy': citas_hoy,
            'proximas_citas': proximas_citas,
            'derivaciones': derivaciones,
            'notificaciones': notificaciones,
        }
        
        return render(request, 'dashboard/medico/dashboard.html', context)
    except Medico.DoesNotExist:
        messages.error(request, 'No se encontrÃ³ el perfil de mÃ©dico')
        return redirect('home')

@login_required
def dashboard_admision(request):
    """Dashboard para personal de admisiÃ³n"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Admision':
        messages.error(request, 'No tienes permiso para acceder a esta pÃ¡gina')
        return redirect('home')
    
    # Obtener citas del dÃ­a
    hoy = timezone.now().date()
    citas_hoy = Cita.objects.filter(
        fecha=hoy,
        estado__in=['pendiente', 'confirmada']
    ).order_by('hora_inicio')
    
    # Obtener pacientes con faltas consecutivas
    pacientes_faltas = Paciente.objects.filter(faltas_consecutivas__gt=0).order_by('-faltas_consecutivas')
    
    # Obtener notificaciones no leÃ­das
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leido=False
    ).order_by('-fecha_envio')[:5]
    
    context = {
        'citas_hoy': citas_hoy,
        'pacientes_faltas': pacientes_faltas,
        'notificaciones': notificaciones,
    }
    
    return render(request, 'dashboard/admision/dashboard.html', context)

@login_required
def dashboard_admin(request):
    """Dashboard para administradores"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Administrador':
        messages.error(request, 'No tienes permiso para acceder a esta pagina')
        return redirect('home')
    
    # EstadÃ­sticas generales
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_citas = Cita.objects.count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    citas_atendidas = Cita.objects.filter(estado='atendida').count()
    
    # Citas por especialidad
    citas_por_especialidad = Cita.objects.values('medico__especialidad__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Obtener notificaciones no leÃ­das
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leido=False
    ).order_by('-fecha_envio')[:5]
    
    context = {
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_atendidas': citas_atendidas,
        'citas_por_especialidad': citas_por_especialidad,
        'notificaciones': notificaciones,
    }
    
    return render(request, 'dashboard/admin/dashboard.html', context)

# API para dashboard dinámico
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    """Endpoint para obtener datos del dashboard según el rol del usuario"""
    user = request.user
    data = {}
    menu = []
    
    # Generar menú según el rol del usuario
    rol_nombre = user.rol.nombre
    
    if rol_nombre == 'Paciente':
        # Datos específicos para pacientes
        try:
            paciente = user.paciente
            
            # Próximas citas
            proximas_citas = Cita.objects.filter(
                paciente=paciente,
                fecha__gte=timezone.now().date(),
                estado__in=['pendiente', 'confirmada']
            ).order_by('fecha', 'hora_inicio')[:5]
            
            data['proximas_citas'] = [{
                'id': cita.id,
                'medico': f"Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos}",
                'especialidad': cita.medico.especialidad.nombre,
                'fecha': cita.fecha.strftime('%d/%m/%Y'),
                'hora': cita.hora_inicio.strftime('%H:%M'),
                'consultorio': cita.consultorio.codigo,
                'estado': cita.get_estado_display()
            } for cita in proximas_citas]
            
            # Notificaciones no leídas
            notificaciones = Notificacion.objects.filter(
                usuario=user,
                leido=False
            ).count()
            
            data['notificaciones_no_leidas'] = notificaciones
            
            # Menú para pacientes
            menu = [
                {'nombre': 'Mis Citas', 'icono': 'fa-calendar-check', 'ruta': '/mis-citas/'},
                {'nombre': 'Reservar Cita', 'icono': 'fa-calendar-plus', 'ruta': '/reservar-cita/'},
                {'nombre': 'Historial Médico', 'icono': 'fa-file-medical-alt', 'ruta': '/mi-historial-medico/'},
                {'nombre': 'Mis Tratamientos', 'icono': 'fa-clipboard-list', 'ruta': '/mis-tratamientos/'},
                {'nombre': 'Mis Derivaciones', 'icono': 'fa-exchange-alt', 'ruta': '/derivaciones/'},
                {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/paciente/'},
                {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
            ]
            
        except Paciente.DoesNotExist:
            return Response({'error': 'Perfil de paciente no encontrado'}, status=404)
            
    elif rol_nombre == 'Medico':
        # Datos específicos para médicos
        try:
            medico = user.medico
            
            # Citas del día
            hoy = timezone.now().date()
            citas_hoy = Cita.objects.filter(
                medico=medico,
                fecha=hoy,
                estado__in=['pendiente', 'confirmada']
            ).order_by('hora_inicio')
            
            data['citas_hoy'] = [{
                'id': cita.id,
                'paciente': f"{cita.paciente.usuario.nombres} {cita.paciente.usuario.apellidos}",
                'hora': cita.hora_inicio.strftime('%H:%M'),
                'consultorio': cita.consultorio.codigo,
                'estado': cita.get_estado_display()
            } for cita in citas_hoy]
            
            # Notificaciones no leídas
            notificaciones = Notificacion.objects.filter(
                usuario=user,
                leido=False
            ).count()
            
            data['notificaciones_no_leidas'] = notificaciones
            
            # Menú para médicos
            menu = [
                {'nombre': 'Mi Agenda', 'icono': 'fa-calendar-alt', 'ruta': '/agenda/'},
                {'nombre': 'Gestión de Citas', 'icono': 'fa-calendar-week', 'ruta': '/gestion-citas/'},
                {'nombre': 'Atender Pacientes', 'icono': 'fa-stethoscope', 'ruta': '/atencion/'},
                {'nombre': 'Gestionar Horario', 'icono': 'fa-clock', 'ruta': '/disponibilidad/'},
                {'nombre': 'Historial Médico', 'icono': 'fa-file-medical', 'ruta': '/historial-medico/'},
                {'nombre': 'Derivar a Especialista', 'icono': 'fa-share', 'ruta': '/derivaciones/'},
                {'nombre': 'Programar Seguimientos', 'icono': 'fa-tasks', 'ruta': '/seguimientos/'},
                {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/medico/'},
                {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
            ]
            
        except Medico.DoesNotExist:
            return Response({'error': 'Perfil de médico no encontrado'}, status=404)
            
    elif rol_nombre == 'Admision':
        # Datos específicos para personal de admisión
        # Citas del día
        hoy = timezone.now().date()
        citas_hoy = Cita.objects.filter(
            fecha=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('hora_inicio')[:10]
        
        data['citas_hoy'] = [{
            'id': cita.id,
            'paciente': f"{cita.paciente.usuario.nombres} {cita.paciente.usuario.apellidos}",
            'medico': f"Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos}",
            'especialidad': cita.medico.especialidad.nombre,
            'hora': cita.hora_inicio.strftime('%H:%M'),
            'consultorio': cita.consultorio.codigo,
            'estado': cita.get_estado_display()
        } for cita in citas_hoy]
        
        # Notificaciones no leídas
        notificaciones = Notificacion.objects.filter(
            usuario=user,
            leido=False
        ).count()
        
        data['notificaciones_no_leidas'] = notificaciones
        
        # Menú para personal de admisión
        menu = [
            {'nombre': 'Registrar Cita', 'icono': 'fa-calendar-plus', 'ruta': '/citas/crear/'},
            {'nombre': 'Buscar Paciente', 'icono': 'fa-search', 'ruta': '/buscar-paciente/'},
            {'nombre': 'Disponibilidad Médica', 'icono': 'fa-clipboard-check', 'ruta': '/disponibilidad/'},
            {'nombre': 'Justificar Inasistencia', 'icono': 'fa-exclamation-triangle', 'ruta': '/inasistencias/'},
            {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/admision/'},
            {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
        ]
        
    elif rol_nombre == 'Administrador':
        # Datos específicos para administradores
        # Estadísticas generales
        total_pacientes = Paciente.objects.count()
        total_medicos = Medico.objects.count()
        total_citas = Cita.objects.count()
        citas_pendientes = Cita.objects.filter(estado='pendiente').count()
        citas_atendidas = Cita.objects.filter(estado='atendida').count()
        
        data['estadisticas'] = {
            'total_pacientes': total_pacientes,
            'total_medicos': total_medicos,
            'total_citas': total_citas,
            'citas_pendientes': citas_pendientes,
            'citas_atendidas': citas_atendidas
        }
        
        # Notificaciones no leídas
        notificaciones = Notificacion.objects.filter(
            usuario=user,
            leido=False
        ).count()
        
        data['notificaciones_no_leidas'] = notificaciones
        
        menu = [
            {
                'nombre': 'Analisis Temporal',
                'icono': 'fa-clock',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'analisisTemporalDropdown',
                'submenus': [
                    {
                        'nombre': 'Distribución de Citas',
                        'icono': 'fa-chart-bar',
                        'ruta': '/administrador/analisis-temporal/distribucion/'
                    },
                    {
                        'nombre': 'Comparativas',
                        'icono': 'fa-chart-line',
                        'ruta': '/administrador/analisis-temporal/comparativas/'
                    },
                    {
                        'nombre': 'Tendencias',
                        'icono': 'fa-chart-area',
                        'ruta': '/administrador/analisis-temporal/tendencias/'
                    },
                    {
                        'nombre': 'Tasas de Asistencia',
                        'icono': 'fa-calendar-check',
                        'ruta': '/administrador/analisis-temporal/asistencia/'
                    }
                ]
            },
            {
                'nombre': 'Analisis por Origen',
                'icono': 'fa-sitemap',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'analisisOrigenDropdown',
                'submenus': [
                    {
                        'nombre': 'Admisión',
                        'icono': 'fa-clipboard-list',
                        'ruta': '/administrador/analisis-origen/admision/'
                    },
                    {
                        'nombre': 'Derivación',
                        'icono': 'fa-share-nodes',
                        'ruta': '/administrador/analisis-origen/derivacion/'
                    },
                    {
                        'nombre': 'Seguimiento',
                        'icono': 'fa-clipboard-check',
                        'ruta': '/administrador/analisis-origen/seguimiento/'
                    }
                ]
            },
            {
                'nombre': 'Analisis por Especialidad',
                'icono': 'fa-stethoscope',
                'ruta': '/administrador/analisis-especialidad/'
            },
            {
                'nombre': 'Análisis por Médico',
                'icono': 'fa-user-md',
                'ruta': '/administrador/analisis-medico/'
            },
            {
                'nombre': 'Analisis de Estado',
                'icono': 'fa-list-check',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'analisisEstadoDropdown',
                'submenus': [
                    {
                        'nombre': 'Citas Completadas',
                        'icono': 'fa-check-circle',
                        'ruta': '/administrador/analisis-estado/completadas/'
                    },
                    {
                        'nombre': 'Citas Canceladas',
                        'icono': 'fa-times-circle',
                        'ruta': '/administrador/analisis-estado/canceladas/'
                    },
                    {
                        'nombre': 'Inasistencias',
                        'icono': 'fa-calendar-xmark',
                        'ruta': '/administrador/analisis-estado/inasistencias/'
                    }
                ]
            },
            {
                'nombre': 'Reportes Especiales',
                'icono': 'fa-file-alt',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'reportesEspecialesDropdown',
                'submenus': [
                    {
                        'nombre': 'Pacientes',
                        'icono': 'fa-users',
                        'ruta': '/administrador/especiales/pacientes/'
                    },
                    {
                        'nombre': 'Satisfacción',
                        'icono': 'fa-smile',
                        'ruta': '/administrador/especiales/satisfaccion/'
                    },
                    {
                        'nombre': 'Indicadores Clave',
                        'icono': 'fa-key',
                        'ruta': '/administrador/especiales/indicadores/'
                    }
                ]
            },
            {
                'nombre': 'Control de Inasistencias',
                'icono': 'fa-calendar-xmark',
                'ruta': '/admin/inasistencias/'
            },
            {
                'nombre': 'Usuarios del Sistema',
                'icono': 'fa-users-gear',
                'ruta': '/admin/usuarios/'
            },
            {
                'nombre': 'Historial Médico',
                'icono': 'fa-notes-medical',
                'ruta': '/admin/historial/'
            },
            {
                'nombre': 'Mi Perfil',
                'icono': 'fa-user',
                'ruta': '/admin/perfil/'
            },
            {
                'nombre': 'Notificaciones',
                'icono': 'fa-bell',
                'ruta': '/admin/notificaciones/'
            },
            {
                'nombre': 'Reportes de farmacia',
                'icono': 'fa-prescription-bottle-medical',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'reportesFarmaciaDropdown',
                'submenus': [
                    {
                        'nombre': 'Consumo de Medicamentos',
                        'icono': 'fa-pills',
                        'ruta': '/administrador/reportes-farmacia/consumo-medicamentos/'
                    }
                ]
            },
        ]
    
    # Incluir menú en la respuesta para todos los roles
    data['menu'] = menu
    
    return Response(data)

# -------------------
# Vistas para tendencias de citas
# -------------------

@login_required
def tendencias_citas(request):
    """
    Vista para la página de análisis de tendencias de citas
    """
    # Verificar permisos del usuario
    if not es_recepcionista(request.user) and not es_administrador(request.user):
        return redirect('inicio')
    # Verificar si el rol es Admin o Administrador y ajustar
    rol_nombre = user.rol.nombre
    es_administrador = rol_nombre in ['Admin', 'Administrador', 'admin', 'administrador']
    
    # Generar menÃº segÃºn el rol
    rol_nombre = user.rol.nombre
    if rol_nombre == 'Paciente':
        # Datos especÃ­ficos para pacientes
        try:
            paciente = user.paciente
            
            # PrÃ³ximas citas
            proximas_citas = Cita.objects.filter(
                paciente=paciente,
                fecha__gte=timezone.now().date(),
                estado__in=['pendiente', 'confirmada']
            ).order_by('fecha', 'hora_inicio')[:5]
            
            data['proximas_citas'] = [{
                'id': cita.id,
                'medico': f"Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos}",
                'especialidad': cita.medico.especialidad.nombre,
                'fecha': cita.fecha.strftime('%d/%m/%Y'),
                'hora': cita.hora_inicio.strftime('%H:%M'),
                'consultorio': cita.consultorio.codigo,
                'estado': cita.get_estado_display()
            } for cita in proximas_citas]
            
            # Notificaciones no leÃ­das
            notificaciones = Notificacion.objects.filter(
                usuario=user,
                leido=False
            ).count()
            
            data['notificaciones_no_leidas'] = notificaciones
            
            # MenÃº para pacientes
            menu = [
                {'nombre': 'Mis Citas', 'icono': 'fa-calendar-check', 'ruta': '/mis-citas/'},
                {'nombre': 'Reservar Cita', 'icono': 'fa-calendar-plus', 'ruta': '/reservar-cita/'},
                {'nombre': 'Historial MÃ©dico', 'icono': 'fa-file-medical-alt', 'ruta': '/mi-historial-medico/'},
                {'nombre': 'Mis Tratamientos', 'icono': 'fa-clipboard-list', 'ruta': '/mis-tratamientos/'},
                {'nombre': 'Mis Derivaciones', 'icono': 'fa-exchange-alt', 'ruta': '/derivaciones/'},
                {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/paciente/'},
                {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
            ]
            
        except Paciente.DoesNotExist:
            return Response({'error': 'Perfil de paciente no encontrado'}, status=404)
            
    elif user.rol.nombre == 'Medico':
        # Datos especÃ­ficos para mÃ©dicos
        try:
            medico = user.medico
            
            # Citas del dÃ­a
            hoy = timezone.now().date()
            citas_hoy = Cita.objects.filter(
                medico=medico,
                fecha=hoy,
                estado__in=['pendiente', 'confirmada']
            ).order_by('hora_inicio')
            
            data['citas_hoy'] = [{
                'id': cita.id,
                'paciente': f"{cita.paciente.usuario.nombres} {cita.paciente.usuario.apellidos}",
                'hora': cita.hora_inicio.strftime('%H:%M'),
                'consultorio': cita.consultorio.codigo,
                'estado': cita.get_estado_display()
            } for cita in citas_hoy]
            
            # Notificaciones no leÃ­das
            notificaciones = Notificacion.objects.filter(
                usuario=user,
                leido=False
            ).count()
            
            data['notificaciones_no_leidas'] = notificaciones
            
            # MenÃº para mÃ©dicos
            menu = [
                {'nombre': 'Mi Agenda', 'icono': 'fa-calendar-alt', 'ruta': '/agenda/'},
                {'nombre': 'GestiÃ³n de Citas', 'icono': 'fa-calendar-week', 'ruta': '/gestion-citas/'},
                {'nombre': 'Atender Pacientes', 'icono': 'fa-stethoscope', 'ruta': '/atencion/'},
                {'nombre': 'Gestionar Horario', 'icono': 'fa-clock', 'ruta': '/disponibilidad/'},
                {'nombre': 'Historial MÃ©dico', 'icono': 'fa-file-medical', 'ruta': '/historial-medico/'},
                {'nombre': 'Derivar a Especialista', 'icono': 'fa-share', 'ruta': '/derivaciones/'},
                {'nombre': 'Programar Seguimientos', 'icono': 'fa-tasks', 'ruta': '/seguimientos/'},
                {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/medico/'},
                {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
            ]
            
            # Incluir menÃº en la respuesta
            data['menu'] = menu
            
        except Medico.DoesNotExist:
            return Response({'error': 'Perfil de mÃ©dico no encontrado'}, status=404)
            
    elif user.rol.nombre == 'Admision':
        # Datos especÃ­ficos para personal de admisiÃ³n
        # Citas del dÃ­a
        hoy = timezone.now().date()
        citas_hoy = Cita.objects.filter(
            fecha=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('hora_inicio')[:10]
        
        data['citas_hoy'] = [{
            'id': cita.id,
            'paciente': f"{cita.paciente.usuario.nombres} {cita.paciente.usuario.apellidos}",
            'medico': f"Dr. {cita.medico.usuario.nombres} {cita.medico.usuario.apellidos}",
            'especialidad': cita.medico.especialidad.nombre,
            'hora': cita.hora_inicio.strftime('%H:%M'),
            'consultorio': cita.consultorio.codigo,
            'estado': cita.get_estado_display()
        } for cita in citas_hoy]
        
        # Notificaciones no leÃ­das
        notificaciones = Notificacion.objects.filter(
            usuario=user,
            leido=False
        ).count()
        
        data['notificaciones_no_leidas'] = notificaciones
        
        # MenÃº para personal de admisiÃ³n
        menu = [
            {'nombre': 'Registrar Cita', 'icono': 'fa-calendar-plus', 'ruta': '/citas/crear/'},
            {'nombre': 'Buscar Paciente', 'icono': 'fa-search', 'ruta': '/buscar-paciente/'},
            {'nombre': 'Disponibilidad MÃ©dica', 'icono': 'fa-clipboard-check', 'ruta': '/disponibilidad/'},
            {'nombre': 'Justificar Inasistencia', 'icono': 'fa-exclamation-triangle', 'ruta': '/inasistencias/'},
            {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/admision/'},
            {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
        ]
        
        # Incluir menÃº en la respuesta
        data['menu'] = menu
        
    elif user.rol.nombre == 'Administrador':
        # Datos especÃ­ficos para administradores
        # EstadÃ­sticas generales
        total_pacientes = Paciente.objects.count()
        total_medicos = Medico.objects.count()
        total_citas = Cita.objects.count()
        citas_pendientes = Cita.objects.filter(estado='pendiente').count()
        citas_atendidas = Cita.objects.filter(estado='atendida').count()
        
        data['estadisticas'] = {
            'total_pacientes': total_pacientes,
            'total_medicos': total_medicos,
            'total_citas': total_citas,
            'citas_pendientes': citas_pendientes,
            'citas_atendidas': citas_atendidas
        }
        
        # Notificaciones no leÃ­das
        notificaciones = Notificacion.objects.filter(
            usuario=user,
            leido=False
        ).count()
        
        data['notificaciones_no_leidas'] = notificaciones
        
        menu = [
            {
                'nombre': 'Analisis Temporal',
                'icono': 'fa-clock',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'analisisTemporalDropdown',
                'submenus': [
                    {
                        'nombre': 'Distribución de Citas',
                        'icono': 'fa-chart-bar',
                        'ruta': '/administrador/analisis-temporal/distribucion/'
                    },
                    {
                        'nombre': 'Comparativas',
                        'icono': 'fa-chart-line',
                        'ruta': '/administrador/analisis-temporal/comparativas/'
                    },
                    {
                        'nombre': 'Tendencias',
                        'icono': 'fa-chart-area',
                        'ruta': '/administrador/analisis-temporal/tendencias/'
                    },
                    {
                        'nombre': 'Tasas de Asistencia',
                        'icono': 'fa-calendar-check',
                        'ruta': '/administrador/analisis-temporal/asistencia/'
                    }
                ]
            },
            {
                'nombre': 'Analisis por Origen',
                'icono': 'fa-sitemap',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'analisisOrigenDropdown',
                'submenus': [
                    {
                        'nombre': 'Admisión',
                        'icono': 'fa-clipboard-list',
                        'ruta': '/administrador/analisis-origen/admision/'
                    },
                    {
                        'nombre': 'Derivación',
                        'icono': 'fa-share-nodes',
                        'ruta': '/administrador/analisis-origen/derivacion/'
                    },
                    {
                        'nombre': 'Seguimiento',
                        'icono': 'fa-clipboard-check',
                        'ruta': '/administrador/analisis-origen/seguimiento/'
                    }
                ]
            },
            {
                'nombre': 'Analisis',
                'icono': 'fa-stethoscope',
                'ruta': '/administrador/analisis-especialidad/'
            },
            {
                'nombre': 'Análisis por Médico',
                'icono': 'fa-user-md',
                'ruta': '/administrador/analisis-medico/'
            },
            {
                'nombre': 'Analisis de Estado',
                'icono': 'fa-list-check',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'analisisEstadoDropdown',
                'submenus': [
                    {
                        'nombre': 'Citas Completadas',
                        'icono': 'fa-check-circle',
                        'ruta': '/administrador/analisis-estado/completadas/'
                    },
                    {
                        'nombre': 'Citas Canceladas',
                        'icono': 'fa-times-circle',
                        'ruta': '/administrador/analisis-estado/canceladas/'
                    },
                    {
                        'nombre': 'Inasistencias',
                        'icono': 'fa-calendar-xmark',
                        'ruta': '/administrador/analisis-estado/inasistencias/'
                    }
                ]
            },
            {
                'nombre': 'Reportes Especiales',
                'icono': 'fa-file-alt',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'reportesEspecialesDropdown',
                'submenus': [
                    {
                        'nombre': 'Pacientes',
                        'icono': 'fa-users',
                        'ruta': '/administrador/especiales/pacientes/'
                    },
                    {
                        'nombre': 'Satisfacción',
                        'icono': 'fa-smile',
                        'ruta': '/administrador/especiales/satisfaccion/'
                    },
                    {
                        'nombre': 'Indicadores Clave',
                        'icono': 'fa-key',
                        'ruta': '/administrador/especiales/indicadores/'
                    }
                ]
            },
            {
                'nombre': 'Control de Inasistencias',
                'icono': 'fa-calendar-xmark',
                'ruta': '/admin/inasistencias/'
            },
            {
                'nombre': 'Usuarios del Sistema',
                'icono': 'fa-users-gear',
                'ruta': '/admin/usuarios/'
            },
            {
                'nombre': 'Historial MÃ©dico',
                'icono': 'fa-notes-medical',
                'ruta': '/admin/historial/'
            },
            {
                'nombre': 'Mi Perfil',
                'icono': 'fa-user',
                'ruta': '/admin/perfil/'
            },
            {
                'nombre': 'Notificaciones',
                'icono': 'fa-bell',
                'ruta': '/admin/notificaciones/'
            },
            {
                'nombre': 'Reportes de farmacia',
                'icono': 'fa-prescription-bottle-medical',
                'ruta': '#',
                'es_desplegable': True,
                'id': 'reportesFarmaciaDropdown',
                'submenus': [
                    {
                        'nombre': 'Consumo de Medicamentos',
                        'icono': 'fa-pills',
                        'ruta': '/administrador/reportes-farmacia/consumo-medicamentos/'
                    }
                ]
            },
        ]
        
    # Incluir menú en la respuesta para todos los roles
    data['menu'] = menu
    
    return Response(data)


# APIs para notificaciones

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_notificacion_leida(request):
    """Marca una notificaciÃ³n como leÃ­da"""
    try:
        data = json.loads(request.body)
        notificacion_id = data.get('notificacion_id')
        
        if not notificacion_id:
            return JsonResponse({'error': 'ID de notificación requerido'}, status=400)
        
        notificacion = get_object_or_404(Notificacion, 
id=notificacion_id, usuario=request.user)
        notificacion.leido = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        
        return JsonResponse({'success': True, 'message': 'Notificaciónmarcada como leÃda'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contador_notificaciones(request):
    """Devuelve el nÃºmero de notificaciones no leÃ­das del usuario"""
    try:
        no_leidas = Notificacion.objects.filter(usuario=request.user, 
leido=False).count()
        return JsonResponse({'success': True, 'no_leidas': no_leidas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Vistas para reportes y análisis estadísticos

@login_required
def comparativas_citas(request):
    """Vista para la página de comparativas de citas"""
    # Verificar que el usuario tenga rol de administrador
    if not request.user.rol or request.user.rol.nombre != 'Administrador':
        messages.error(request, 'No tienes permisos para acceder a esta página')
        return redirect('dashboard_view')
    
    # Obtener todas las especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Configurar fechas predeterminadas (mes actual)
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    ultimo_dia_mes = (primer_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # Información para el menú lateral y panel de administrador
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_citas = Cita.objects.count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    citas_atendidas = Cita.objects.filter(estado='atendida').count()
    
    citas_por_especialidad = Cita.objects.values('medico__especialidad__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    notificaciones = Notificacion.objects.filter(
        usuario=request.user,
        leido=False
    ).order_by('-fecha_envio')[:5]
    
    # Contexto para la plantilla
    context = {
        'titulo': 'Comparativas de Citas',
        'especialidades': especialidades,
        'fecha_inicio': primer_dia_mes,
        'fecha_fin': ultimo_dia_mes,
        
        # Datos para el menú lateral y dashboard
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_atendidas': citas_atendidas,
        'citas_por_especialidad': citas_por_especialidad,
        'notificaciones': notificaciones,
    }
    
    return render(request, 'admin/comparativas_citas.html', context)

@login_required
def api_comparativa_citas(request):
    """
    API para entregar datos comparativos de citas entre dos períodos.
    También puede incluir dimensiones adicionales de análisis como: especialidad, día de la semana y horario.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Verificar que el usuario tenga rol de administrador
        if not request.user.rol or request.user.rol.nombre != 'Administrador':
            logger.warning(f"Acceso denegado: Usuario {request.user.username} no tiene rol de Administrador")
            return JsonResponse({'error': 'No tienes permisos para acceder a esta información', 'status': 'error'}, status=403)
            
        # Preparar logger para seguimiento detallado
        logger.info("API comparativa_citas - Iniciando procesamiento")
    
        # Log de parámetros recibidos en la petición
        logger.info(f"API comparativa_citas - Parámetros recibidos: {request.GET}")
        
        # Obtener parámetros de filtro para el primer período
        periodo1 = request.GET.get('periodo1', 'mensual')
        fecha_inicio1 = request.GET.get('fecha_inicio1')
        fecha_fin1 = request.GET.get('fecha_fin1')
        
        # Obtener parámetros de filtro para el segundo período
        periodo2 = request.GET.get('periodo2', 'mensual')
        fecha_inicio2 = request.GET.get('fecha_inicio2')
        fecha_fin2 = request.GET.get('fecha_fin2')
        
        # Filtros comunes
        especialidad_id = request.GET.get('especialidad', '')
        medico_id = request.GET.get('medico', '')
        
        # Verificar si se solicitan dimensiones adicionales
        incluir_dimensiones = request.GET.get('incluir_dimensiones') == 'true'
        
        logger.info(f"Parámetros procesados: periodo1={periodo1}, fecha_inicio1={fecha_inicio1}, fecha_fin1={fecha_fin1}, periodo2={periodo2}, fecha_inicio2={fecha_inicio2}, fecha_fin2={fecha_fin2}, especialidad={especialidad_id}, medico={medico_id}, incluir_dimensiones={incluir_dimensiones}")
        
        # Convertir fechas a objetos date
        fecha_inicio1 = datetime.strptime(fecha_inicio1, '%Y-%m-%d').date() if fecha_inicio1 else None
        fecha_fin1 = datetime.strptime(fecha_fin1, '%Y-%m-%d').date() if fecha_fin1 else None
        fecha_inicio2 = datetime.strptime(fecha_inicio2, '%Y-%m-%d').date() if fecha_inicio2 else None
        fecha_fin2 = datetime.strptime(fecha_fin2, '%Y-%m-%d').date() if fecha_fin2 else None
        
        # Función para obtener datos de citas según filtros
        def obtener_datos_periodo(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            import logging
            logger = logging.getLogger(__name__)
            
            # Log de parámetros recibidos
            logger.info(f"obtener_datos_periodo - Parámetros: fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}, especialidad_id={especialidad_id}, medico_id={medico_id}")
            
            # Consulta base para citas
            query = Cita.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            logger.info(f"Citas encontradas en rango de fechas: {query.count()}")
            
            # Aplicar filtros adicionales si se proporcionan y son válidos
            # Si especialidad_id es '0' o 'Todas', no aplicar filtro (mostrar todas)
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                query = query.filter(medico__especialidad_id=especialidad_id)
                logger.info(f"Aplicando filtro de especialidad {especialidad_id}, citas restantes: {query.count()}")
            else:
                logger.info(f"No se aplica filtro de especialidad, valor recibido: {especialidad_id}")
            
            # Si medico_id es '0' o 'Todos', no aplicar filtro (mostrar todos)
            if medico_id and medico_id not in ['0', 'Todos'] and medico_id.isdigit():
                query = query.filter(medico__id=medico_id)  # Corregido: medico__id en lugar de medico_id
                logger.info(f"Aplicando filtro de médico {medico_id}, citas restantes: {query.count()}")
            else:
                logger.info(f"No se aplica filtro de médico, valor recibido: {medico_id}")
            
            # Contar citas por estado (usando los nombres exactos de la base de datos, en minúsculas)
            pendientes = query.filter(estado='pendiente').count()
            confirmadas = query.filter(estado='confirmada').count()
            atendidas = query.filter(estado='atendida').count()
            canceladas = query.filter(estado='cancelada').count()
            
            # Total de citas
            total = pendientes + confirmadas + atendidas + canceladas
            
            # Log con resultados finales
            logger.info(f"Resultados finales: total={total}, pendientes={pendientes}, confirmadas={confirmadas}, atendidas={atendidas}, canceladas={canceladas}")
            
            # Calcular porcentaje de asistencia (citas atendidas dividido por el total)
            porcentaje_asistencia = round((atendidas / total) * 100, 2) if total > 0 else 0
            
            return {
                'total': total,
                'pendientes': pendientes,
                'confirmadas': confirmadas,  # Nuevo estado
                'atendidas': atendidas,
                'canceladas': canceladas,
                'porcentaje_asistencia': porcentaje_asistencia
            }
        
        # Función para obtener datos por especialidad
        def obtener_datos_especialidades(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            logger.info(f"Obteniendo datos por especialidad: periodo {fecha_inicio} - {fecha_fin}")
            
            # Si se ha seleccionado una especialidad específica, no tiene sentido mostrar la comparativa por especialidades
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                logger.info(f"Se ha seleccionado una especialidad específica ({especialidad_id}), no se muestra comparativa por especialidades")
                return []
            
            # En lugar de buscar a través de la relación inversa compleja, primero obtenemos todos los médicos con citas
            # y luego obtenemos sus especialidades
            ids_medicos_con_citas = Cita.objects.filter(
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin
            ).values_list('medico', flat=True).distinct()
            
            # Ahora obtenemos las especialidades de esos médicos
            especialidades = Especialidad.objects.filter(
                medicos__id__in=ids_medicos_con_citas
            ).distinct()
            
            logger.info(f"Encontradas {especialidades.count()} especialidades con citas en el período")
            
            resultados = []
            
            for especialidad in especialidades:
                query = Cita.objects.filter(
                    fecha__gte=fecha_inicio, 
                    fecha__lte=fecha_fin,
                    medico__especialidad=especialidad
                )
                
                if medico_id and medico_id not in ['0', 'Todos'] and medico_id.isdigit():
                    query = query.filter(medico__id=medico_id)  # Corregido: medico__id en lugar de medico_id
                    
                pendientes = query.filter(estado='pendiente').count()
                confirmadas = query.filter(estado='confirmada').count()
                atendidas = query.filter(estado='atendida').count()
                canceladas = query.filter(estado='cancelada').count()
                total = pendientes + confirmadas + atendidas + canceladas
                
                # Solo incluir especialidades con citas
                if total > 0:
                    porcentaje_asistencia = round((atendidas / total) * 100, 2)
                    
                    resultados.append({
                        'id': especialidad.id,
                        'nombre': especialidad.nombre,
                        'total': total,
                        'pendientes': pendientes,
                        'confirmadas': confirmadas,
                        'atendidas': atendidas,
                        'canceladas': canceladas,
                        'porcentaje_asistencia': porcentaje_asistencia
                    })
            
            # Ordenar por porcentaje de asistencia (descendente)
            return sorted(resultados, key=lambda x: x['porcentaje_asistencia'], reverse=True)
        
        # Función para obtener datos por día de la semana
        def obtener_datos_dias_semana(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            logger.info(f"Obteniendo datos por día de la semana: periodo {fecha_inicio} - {fecha_fin}")
            
            dias_semana = {
                'lunes': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'martes': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'miércoles': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'jueves': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'viernes': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'sábado': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'domingo': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0}
            }
            
            # Obtener todas las citas en el período
            query = Cita.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            
            # Aplicar filtros adicionales si se proporcionan y son válidos
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                query = query.filter(medico__especialidad_id=especialidad_id)
            
            if medico_id and medico_id not in ['0', 'Todos'] and medico_id.isdigit():
                query = query.filter(medico__id=medico_id)  # Corregido: medico__id en lugar de medico_id
            
            logger.info(f"Analizando {query.count()} citas para datos por día de la semana")
            
            # Para cada cita, incrementar el contador correspondiente
            for cita in query:
                # Convertir número de día de semana (0-6, donde 0 es lunes) a nombre
                nombres_dias = ['lunes', 'martes', 'miércoles', 'jueves', 'viernes', 'sábado', 'domingo']
                dia_semana = nombres_dias[cita.fecha.weekday()]
                
                # Mapear el estado singular al plural para incrementar el contador correcto
                mapeo_estados = {
                    'pendiente': 'pendientes',
                    'confirmada': 'confirmadas',
                    'atendida': 'atendidas',
                    'cancelada': 'canceladas'
                }
                
                # Incrementar contador usando el mapeo
                if cita.estado in mapeo_estados:
                    dias_semana[dia_semana][mapeo_estados[cita.estado]] += 1
                    dias_semana[dia_semana]['total'] += 1
                else:
                    logger.warning(f"Estado de cita no reconocido: {cita.estado}")
            
            return dias_semana
        
        # Función para obtener datos por horario (mañana vs tarde)
        def obtener_datos_horarios(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            logger.info(f"Obteniendo datos por horario: periodo {fecha_inicio} - {fecha_fin}")
            
            # Definir horarios (12:00 como límite entre mañana y tarde)
            horarios = {
                'mañana': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'tarde': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0}
            }
            
            # Obtener todas las citas en el período
            query = Cita.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            
            # Aplicar filtros adicionales si se proporcionan y son válidos
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                query = query.filter(medico__especialidad_id=especialidad_id)
            
            if medico_id and medico_id not in ['0', 'Todos'] and medico_id.isdigit():
                query = query.filter(medico__id=medico_id)  # Corregido: medico__id en lugar de medico_id
            
            logger.info(f"Analizando {query.count()} citas para datos por horario")
            
            # Para cada cita, incrementar el contador correspondiente
            for cita in query:
                # Determinar si es mañana o tarde basado en la hora_inicio
                horario = 'mañana' if cita.hora_inicio.hour < 12 else 'tarde'
                
                # Mapear el estado singular al plural para incrementar el contador correcto
                mapeo_estados = {
                    'pendiente': 'pendientes',
                    'confirmada': 'confirmadas',
                    'atendida': 'atendidas',
                    'cancelada': 'canceladas'
                }
                
                # Incrementar contador usando el mapeo
                if cita.estado in mapeo_estados:
                    horarios[horario][mapeo_estados[cita.estado]] += 1
                    horarios[horario]['total'] += 1
                else:
                    logger.warning(f"Estado de cita no reconocido: {cita.estado}")
            
            return horarios
        
        # Obtener datos para ambos períodos
        datos_periodo1 = obtener_datos_periodo(fecha_inicio1, fecha_fin1, especialidad_id, medico_id)
        datos_periodo2 = obtener_datos_periodo(fecha_inicio2, fecha_fin2, especialidad_id, medico_id)
        
        # Calcular variaciones entre períodos
        variaciones = {
            'total': datos_periodo2['total'] - datos_periodo1['total'],
            'pendientes': datos_periodo2['pendientes'] - datos_periodo1['pendientes'],
            'confirmadas': datos_periodo2['confirmadas'] - datos_periodo1['confirmadas'],
            'atendidas': datos_periodo2['atendidas'] - datos_periodo1['atendidas'],
            'canceladas': datos_periodo2['canceladas'] - datos_periodo1['canceladas'],
            'porcentaje_asistencia': datos_periodo2['porcentaje_asistencia'] - datos_periodo1['porcentaje_asistencia']
        }
        
        # Validación exhaustiva de datos para evitar errores
        for periodo in [datos_periodo1, datos_periodo2]:
            # Verificar y establecer valores predeterminados para todos los campos necesarios
            campos_requeridos = ['pendientes', 'confirmadas', 'atendidas', 'canceladas', 'total', 'porcentaje_asistencia']
            for key in campos_requeridos:
                if key not in periodo or periodo[key] is None:
                    logger.warning(f"Campo {key} faltante o nulo en datos del período, estableciendo a 0")
                    periodo[key] = 0
                    
            # Verificación adicional del porcentaje de asistencia
            if periodo['total'] > 0:
                # Recalcular porcentaje de asistencia por si acaso
                periodo['porcentaje_asistencia'] = round((periodo['atendidas'] / periodo['total']) * 100, 2)
            else:
                periodo['porcentaje_asistencia'] = 0
                
            logger.info(f"Datos del período validados: {periodo}")

        # Registrar en el log las variaciones calculadas
        logger.info(f"Variaciones calculadas entre periodos: {variaciones}")
        
        # Calcular variaciones porcentuales
        variaciones_porcentuales = {}
        for key, value in variaciones.items():
            # Si es el porcentaje de asistencia, solo copiar el valor de la variación
            if key == 'porcentaje_asistencia':
                variaciones_porcentuales[key] = round(value, 2)
            # Para los demás, calcular la variación porcentual si hay datos en el primer período
            elif datos_periodo1[key] > 0:
                variaciones_porcentuales[key] = round((value / datos_periodo1[key]) * 100, 2)
            # Si no hay datos en el primer período pero hay una variación, ponerla como 100%
            elif value > 0:
                variaciones_porcentuales[key] = 100.0
            # Si no hay datos en ninguno de los períodos, la variación es 0
            else:
                variaciones_porcentuales[key] = 0.0
        
        logger.info(f"Variaciones porcentuales calculadas: {variaciones_porcentuales}")
        
        # Verificar si hay datos (al menos una cita en alguno de los periodos)
        if datos_periodo1['total'] > 0 or datos_periodo2['total'] > 0:
            # Preparar respuesta con datos
            response = {
                'periodo1': {
                    'etiqueta': f"{periodo1.capitalize()}: {fecha_inicio1} - {fecha_fin1}",
                    'datos': datos_periodo1
                },
                'periodo2': {
                    'etiqueta': f"{periodo2.capitalize()}: {fecha_inicio2} - {fecha_fin2}",
                    'datos': datos_periodo2
                },
                'variaciones': variaciones,
                'variaciones_porcentuales': variaciones_porcentuales,
                'status': 'success'
            }
            logger.info(f"API comparativa_citas - Devolviendo datos con éxito: {datos_periodo1['total']} citas en periodo 1, {datos_periodo2['total']} citas en periodo 2")
        else:
            # No hay datos, pero aun así devolver una estructura válida para evitar errores en el frontend
            response = {
                'periodo1': {
                    'etiqueta': f"{periodo1.capitalize()}: {fecha_inicio1} - {fecha_fin1}",
                    'datos': datos_periodo1
                },
                'periodo2': {
                    'etiqueta': f"{periodo2.capitalize()}: {fecha_inicio2} - {fecha_fin2}",
                    'datos': datos_periodo2
                },
                'variaciones': variaciones,
                'variaciones_porcentuales': variaciones_porcentuales,
                'status': 'success',
                'message': 'No se encontraron citas para los períodos y filtros seleccionados'
            }
            logger.warning(f"API comparativa_citas - No se encontraron citas para los filtros seleccionados")
        
        # Agregar dimensiones adicionales si se solicitan
        if incluir_dimensiones:
            logger.info("Se solicitaron dimensiones adicionales, procesando datos...")
            
            # Combinar datos de ambos períodos para las dimensiones adicionales
            # (Usar el rango de fechas más amplio entre los dos períodos)
            fecha_inicio_combinada = min(fecha_inicio1, fecha_inicio2)
            fecha_fin_combinada = max(fecha_fin1, fecha_fin2)
            
            logger.info(f"Rango combinado para dimensiones adicionales: {fecha_inicio_combinada} - {fecha_fin_combinada}")
            
            # Obtener datos para las diferentes dimensiones
            datos_especialidades = obtener_datos_especialidades(fecha_inicio_combinada, fecha_fin_combinada, especialidad_id, medico_id)
            datos_dias_semana = obtener_datos_dias_semana(fecha_inicio_combinada, fecha_fin_combinada, especialidad_id, medico_id)
            datos_horarios = obtener_datos_horarios(fecha_inicio_combinada, fecha_fin_combinada, especialidad_id, medico_id)
            
            # Añadir datos a la respuesta
            response['dimensiones_adicionales'] = {
                'especialidades': datos_especialidades,
                'dias_semana': datos_dias_semana,
                'horarios': datos_horarios
            }
            
            logger.info(f"Datos de dimensiones adicionales agregados: {len(datos_especialidades)} especialidades, {len(datos_dias_semana)} días, {len(datos_horarios)} horarios")
        
        return JsonResponse(response)
    
    except Exception as e:
        import traceback
        import sys
        # Obtener la traza completa del error
        exc_type, exc_value, exc_traceback = sys.exc_info()
        # Convertir la traza en texto para el log
        trace_details = traceback.format_exception(exc_type, exc_value, exc_traceback)
        # Registrar el error completo en el log
        logger.error(f"Error en api_comparativa_citas: {str(e)}")
        logger.error(f"Traza completa: {''.join(trace_details)}")
        
        # Devolver una respuesta con estructura segura que no causará errores en el frontend
        # Generamos una respuesta mínima pero válida que el frontend puede manejar
        periodo_vacio = {
            'total': 0,
            'pendientes': 0,
            'confirmadas': 0,
            'atendidas': 0,
            'canceladas': 0,
            'porcentaje_asistencia': 0
        }
        
        return JsonResponse({
            'periodo1': {
                'etiqueta': 'Periodo 1',
                'datos': periodo_vacio
            },
            'periodo2': {
                'etiqueta': 'Periodo 2',
                'datos': periodo_vacio
            },
            'variaciones': {
                'total': 0,
                'pendientes': 0,
                'confirmadas': 0,
                'atendidas': 0,
                'canceladas': 0,
                'porcentaje_asistencia': 0
            },
            'variaciones_porcentuales': {
                'total': 0,
                'pendientes': 0,
                'confirmadas': 0,
                'atendidas': 0,
                'canceladas': 0,
                'porcentaje_asistencia': 0
            },
            'error': f"Error: {str(e)}",
            'tipo_error': exc_type.__name__,
            'status': 'error',
            'message': 'Ocurrió un error al procesar los datos. Se muestran datos vacíos como respaldo.'
        }, status=200)  # Devolver 200 en lugar de 500 para que el frontend aún lo muestre


@login_required
def api_medicos_por_especialidad(request):
    """
    API endpoint para obtener médicos filtrados por especialidad.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Obtener el ID de la especialidad de la petición
    especialidad_id = request.GET.get('especialidad_id', '0')
    logger.info(f"API medicos_por_especialidad llamada con especialidad_id={especialidad_id}")
    
    # Lista para almacenar los médicos
    medicos_lista = []
    
    try:
        # Si se seleccionó una especialidad específica (diferente de 'Todas')
        if especialidad_id and especialidad_id != '0':
            # Consultar los médicos que pertenecen a esa especialidad
            medicos = Medico.objects.filter(especialidad_id=especialidad_id)
            logger.info(f"Encontrados {medicos.count()} médicos para la especialidad {especialidad_id}")
        else:
            # Si no se seleccionó especialidad o se seleccionó 'Todas', mostrar todos los médicos
            medicos = Medico.objects.all()
            logger.info(f"Mostrando todos los médicos: {medicos.count()} encontrados")
        
        # Formatear datos para el frontend
        for medico in medicos:
            nombre_completo = f"{medico.usuario.nombres} {medico.usuario.apellidos}"
            medico_data = {
                'id': medico.id,
                'nombre_completo': nombre_completo
            }
            medicos_lista.append(medico_data)
    
    except Exception as e:
        logger.error(f"Error al obtener médicos: {str(e)}")
        return JsonResponse({'medicos': [], 'error': str(e), 'status': 'error'})
    
    # Devolver la lista de médicos en formato JSON
    response = {
        'medicos': medicos_lista,
        'status': 'success',
        'count': len(medicos_lista),
        'especialidad_id': especialidad_id
    }
    
    return JsonResponse(response)

# Imports adicionales para reportes
from django.http import JsonResponse
from datetime import timedelta
import logging
logger = logging.getLogger(__name__)


@login_required
def tasas_asistencia(request):
    """
    Vista para la página de análisis de tasas de asistencia y recuperación
    """
    # Solo accesible para administradores
    if not request.user.rol or request.user.rol.nombre != 'Administrador':
        messages.error(request, 'No tiene permisos para acceder a esta sección')
        return redirect('dashboard_view')
    
    # Obtener todas las especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Renderizar la plantilla
    return render(request, 'admin/tasas_asistencia.html', {
        'especialidades': especialidades
    })


@login_required
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_tasas_asistencia(request):
    """
    API para obtener datos de tasas de asistencia y recuperación
    """
    try:
        # Obtener parámetros de la solicitud
        fecha_inicio = request.GET.get('fecha_inicio', None)
        fecha_fin = request.GET.get('fecha_fin', None)
        especialidad_id = request.GET.get('especialidad_id', '0')
        medico_id = request.GET.get('medico_id', '0')
        
        # Validar fechas
        if not fecha_inicio or not fecha_fin:
            # Si no se especifican fechas, usar últimos 3 meses
            fecha_fin = timezone.now().date()
            fecha_inicio = fecha_fin - timedelta(days=90)
        else:
            # Convertir strings a objetos date
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': 'Formato de fecha inválido. Use YYYY-MM-DD',
                    'status': 'error'
                }, status=400)
        
        # Construir filtro base para las citas
        filtro_citas = Q(fecha__gte=fecha_inicio) & Q(fecha__lte=fecha_fin)
        
        # Aplicar filtros adicionales si se especifican
        if especialidad_id and especialidad_id != '0':
            filtro_citas &= Q(medico__especialidad_id=especialidad_id)
        
        if medico_id and medico_id != '0':
            filtro_citas &= Q(medico_id=medico_id)
        
        # Obtener todas las citas según los filtros
        citas = Cita.objects.filter(filtro_citas)
        
        # Calcular métricas básicas
        total_citas = citas.count()
        citas_atendidas = citas.filter(estado='atendida').count()
        citas_pendientes = citas.filter(estado='pendiente').count()
        citas_confirmadas = citas.filter(estado='confirmada').count()
        citas_canceladas = citas.filter(estado='cancelada').count()
        
        # Cálculo de tasas
        tasa_asistencia = (citas_atendidas / total_citas * 100) if total_citas > 0 else 0
        tasa_inasistencia = (citas_confirmadas / total_citas * 100) if total_citas > 0 else 0
        tasa_cancelacion = (citas_canceladas / total_citas * 100) if total_citas > 0 else 0
        
        # Calcular métricas de recuperación de inasistencias
        # Identificar citas con inasistencia (confirmadas que no fueron atendidas)
        inasistencias = citas.filter(estado='confirmada', asistio=False)
        inasistencias_totales = inasistencias.count()
        
        # Identificar cuántas de estas inasistencias tienen citas de seguimiento que sí fueron atendidas
        inasistencias_recuperadas = 0
        for cita in inasistencias:
            # Verificar si esta cita tiene alguna cita de seguimiento que fue atendida
            if cita.citas_seguimiento.filter(estado='atendida').exists():
                inasistencias_recuperadas += 1
        
        # Calcular tasa de recuperación
        tasa_recuperacion = (inasistencias_recuperadas / inasistencias_totales * 100) if inasistencias_totales > 0 else 0
        
        # Calcular evolución mensual
        # Dividir el período en 6 intervalos para mostrar evolución
        dias_totales = (fecha_fin - fecha_inicio).days
        intervalo_dias = max(dias_totales // 6, 1)  # Al menos 1 día por intervalo
        
        etiquetas = []
        datos_asistencia = []
        datos_recuperacion = []
        
        for i in range(6):
            intervalo_inicio = fecha_inicio + timedelta(days=i * intervalo_dias)
            if i < 5:
                intervalo_fin = fecha_inicio + timedelta(days=(i + 1) * intervalo_dias - 1)
            else:
                intervalo_fin = fecha_fin
            
            if intervalo_inicio > fecha_fin:
                break
            
            # Etiquetar el intervalo
            etiqueta = f"{intervalo_inicio.strftime('%d/%m')} - {intervalo_fin.strftime('%d/%m')}"
            etiquetas.append(etiqueta)
            
            # Filtrar citas para este intervalo
            citas_intervalo = citas.filter(fecha__gte=intervalo_inicio, fecha__lte=intervalo_fin)
            total_intervalo = citas_intervalo.count()
            atendidas_intervalo = citas_intervalo.filter(estado='atendida').count()
            
            # Calcular tasa de asistencia del intervalo
            tasa_asistencia_intervalo = (atendidas_intervalo / total_intervalo * 100) if total_intervalo > 0 else 0
            datos_asistencia.append(tasa_asistencia_intervalo)
            
            # Calcular tasa de recuperación del intervalo
            inasistencias_intervalo = citas_intervalo.filter(estado='confirmada', asistio=False)
            inasistencias_intervalo_count = inasistencias_intervalo.count()
            
            recuperadas_intervalo = 0
            for cita in inasistencias_intervalo:
                if cita.citas_seguimiento.filter(estado='atendida').exists():
                    recuperadas_intervalo += 1
            
            tasa_recuperacion_intervalo = (recuperadas_intervalo / inasistencias_intervalo_count * 100) if inasistencias_intervalo_count > 0 else 0
            datos_recuperacion.append(tasa_recuperacion_intervalo)
        
        # Preparar respuesta
        response = {
            'tasas': {
                'asistencia': tasa_asistencia,
                'inasistencia': tasa_inasistencia,
                'cancelacion': tasa_cancelacion,
                'recuperacion': tasa_recuperacion
            },
            'cantidades': {
                'total': total_citas,
                'atendidas': citas_atendidas,
                'pendientes': citas_pendientes,
                'confirmadas': citas_confirmadas,
                'canceladas': citas_canceladas
            },
            'recuperacion': {
                'inasistencias_totales': inasistencias_totales,
                'inasistencias_recuperadas': inasistencias_recuperadas
            },
            'evolucion': {
                'etiquetas': etiquetas,
                'asistencia': datos_asistencia,
                'recuperacion': datos_recuperacion
            },
            'status': 'success'
        }
        
        return Response(response)
    
    except Exception as e:
        logger.error(f"Error en api_tasas_asistencia: {str(e)}")
        import traceback
        logger.error(traceback.format_exc())
        
        return Response({
            'error': str(e),
            'status': 'error',
            'tasas': {
                'asistencia': 0,
                'inasistencia': 0,
                'cancelacion': 0,
                'recuperacion': 0
            },
            'cantidades': {
                'total': 0,
                'atendidas': 0,
                'pendientes': 0,
                'confirmadas': 0,
                'canceladas': 0
            },
            'recuperacion': {
                'inasistencias_totales': 0,
                'inasistencias_recuperadas': 0
            },
            'evolucion': {
                'etiquetas': [],
                'asistencia': [],
                'recuperacion': []
            }
        }, status=200)  # Usar 200 para que el frontend pueda mostrar el mensaje de error

def reporte_consumo_medicamentos(request):
    if not request.user.is_authenticated or not user_is_admin(request.user):
        return render(request, '403.html')
    filtro = request.GET.get('filtro', 'mes')
    periodo = request.GET.get('periodo')
    hoy = datetime.now()
    qs = DetalleReceta.objects.select_related('medicamento', 'receta')
    if filtro == 'mes' and periodo:
        anio, mes = map(int, periodo.split('-'))
        qs = qs.filter(receta__fecha_prescripcion__year=anio, receta__fecha_prescripcion__month=mes)
    elif filtro == 'trimestre' and periodo:
        anio, trimestre = map(int, periodo.split('-'))
        meses = [(1,3), (4,6), (7,9), (10,12)][int(trimestre)-1]
        qs = qs.filter(receta__fecha_prescripcion__year=anio, receta__fecha_prescripcion__month__gte=meses[0], receta__fecha_prescripcion__month__lte=meses[1])
    elif filtro == 'anio' and periodo:
        anio = int(periodo)
        qs = qs.filter(receta__fecha_prescripcion__year=anio)
    top = (qs.values('medicamento__nombre_comercial')
             .annotate(total=Sum('cantidad_prescrita'))
             .order_by('-total')[:10])
    labels = [x['medicamento__nombre_comercial'] for x in top]
    data = [x['total'] for x in top]
    return JsonResponse({'labels': labels, 'data': data})

def admin_reporte_consumo_medicamentos(request):
    if not request.user.is_authenticated or not user_is_admin(request.user):
        return render(request, '403.html')
    if request.headers.get('x-requested-with') == 'XMLHttpRequest' or request.GET.get('filtro'):
        return reporte_consumo_medicamentos(request)
    return render(request, 'admin/reportes_farmacia_consumo.html', {'now': timezone.now()})

def user_is_admin(user):
    return user.is_superuser or (hasattr(user, 'rol') and user.rol and user.rol.nombre == 'Administrador')

