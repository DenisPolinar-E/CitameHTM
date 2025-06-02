
from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth import login, authenticate, logout
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_POST
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from .models import *
from .forms import *
import json
from datetime import datetime, timedelta

# Vistas pÃƒÂºblicas
def home(request):
    """Vista de la pÃƒÂ¡gina de bienvenida"""
    return render(request, 'home.html')

def login_view(request):
    """Vista de inicio de sesiÃƒÂ³n"""
    if request.method == 'POST':
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        user = authenticate(request, username=dni, password=password)
        
        if user is not None:
            login(request, user)
            
            # RedirecciÃƒÂ³n segÃƒÂºn el rol del usuario
            if user.rol:
                if user.rol.nombre == 'Paciente':
                    return redirect('dashboard_paciente')
                elif user.rol.nombre == 'Medico':
                    return redirect('dashboard_medico')
                elif user.rol.nombre == 'Admision':
                    return redirect('dashboard_admision')
                elif user.rol.nombre == 'Administrador':
                    return redirect('dashboard_admin')
            
            # Si no tiene rol asignado, redirigir a la pÃƒÂ¡gina principal
            return redirect('home')
        else:
            messages.error(request, 'DNI o contraseÃƒÂ±a incorrectos')
    
    return render(request, 'auth/login.html')

def registro_view(request):
    """Vista de registro de usuarios con selecciÃƒÂ³n de rol"""
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
            
            # Crear perfil segÃƒÂºn el rol
            if rol_nombre == 'Paciente':
                Paciente.objects.create(usuario=user)
            elif rol_nombre == 'Medico':
                # Para mÃƒÂ©dicos, usar la especialidad seleccionada o una por defecto
                from .models import Medico
                especialidad_id = request.POST.get('especialidad')
                
                try:
                    if especialidad_id and especialidad_id.isdigit():
                        especialidad = Especialidad.objects.get(id=especialidad_id)
                    else:
                        # Si no se seleccionÃƒÂ³ especialidad, usar General como predeterminada
                        especialidad, _ = Especialidad.objects.get_or_create(nombre='General')
                except Especialidad.DoesNotExist:
                    especialidad, _ = Especialidad.objects.get_or_create(nombre='General')
                
                # Asignar un CMP provisional que se actualizarÃƒÂ¡ despuÃƒÂ©s
                cmp_provisional = f"TEMP-{user.dni}"
                Medico.objects.create(usuario=user, especialidad=especialidad, cmp=cmp_provisional)
            
            # Iniciar sesiÃƒÂ³n automÃƒÂ¡ticamente
            login(request, user)
            messages.success(request, f'Â¡Registro exitoso como {rol_nombre}! Bienvenido al sistema.')
            
            # Redireccionar segÃƒÂºn el rol
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
    """Cerrar sesiÃƒÂ³n"""
    logout(request)
    return redirect('home')

# Vistas protegidas por rol
@login_required
def dashboard_view(request):
    """Redirecciona al dashboard especÃƒÂ­fico segÃƒÂºn el rol del usuario"""
    if request.user.rol:
        if request.user.rol.nombre == 'Paciente':
            return redirect('dashboard_paciente')
        elif request.user.rol.nombre == 'Medico':
            return redirect('dashboard_medico')
        elif request.user.rol.nombre == 'Admision':
            return redirect('dashboard_admision')
        elif request.user.rol.nombre == 'Administrador':
            return redirect('dashboard_admin')
    
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
        
        # Obtener prÃƒÂ³ximas citas
        proximas_citas = Cita.objects.filter(
            paciente=paciente,
            fecha__gte=timezone.now().date(),
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora_inicio')[:5]
        
        # Obtener historial mÃƒÂ©dico
        historial = HistorialMedico.objects.filter(paciente=paciente).order_by('-fecha')[:5]
        
        # Obtener derivaciones activas
        derivaciones = Derivacion.objects.filter(
            paciente=paciente,
            estado='pendiente',
            fecha_derivacion__gte=timezone.now().date() - timedelta(days=30)
        )
        
        # Obtener notificaciones no leÃƒÂ­das
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
    """Dashboard para mÃƒÂ©dicos"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta pgina')
        return redirect('home')
    
    try:
        medico = request.user.medico
        
        # Obtener citas del dÃƒÂ­a
        hoy = timezone.now().date()
        citas_hoy = Cita.objects.filter(
            medico=medico,
            fecha=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('hora_inicio')
        
        # Obtener prÃƒÂ³ximas citas (excluyendo hoy)
        proximas_citas = Cita.objects.filter(
            medico=medico,
            fecha__gt=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora_inicio')[:10]
        
        # Obtener derivaciones realizadas recientemente
        derivaciones = Derivacion.objects.filter(
            medico_origen=medico
        ).order_by('-fecha_derivacion')[:5]
        
        # Obtener notificaciones no leÃƒÂ­das
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
        messages.error(request, 'No se encontrÃƒÂ³ el perfil de mÃƒÂ©dico')
        return redirect('home')

@login_required
def dashboard_admision(request):
    """Dashboard para personal de admisiÃƒÂ³n"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Admision':
        messages.error(request, 'No tienes permiso para acceder a esta pÃƒÂ¡gina')
        return redirect('home')
    
    # Obtener citas del dÃƒÂ­a
    hoy = timezone.now().date()
    citas_hoy = Cita.objects.filter(
        fecha=hoy,
        estado__in=['pendiente', 'confirmada']
    ).order_by('hora_inicio')
    
    # Obtener pacientes con faltas consecutivas
    pacientes_faltas = Paciente.objects.filter(faltas_consecutivas__gt=0).order_by('-faltas_consecutivas')
    
    # Obtener notificaciones no leÃƒÂ­das
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
    
    # EstadÃƒÂ­sticas generales
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_citas = Cita.objects.count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    citas_atendidas = Cita.objects.filter(estado='atendida').count()
    
    # Citas por especialidad
    citas_por_especialidad = Cita.objects.values('medico__especialidad__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Obtener notificaciones no leÃƒÂ­das
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

# API para dashboard dinÃ¡mico
@api_view(['GET'])
@permission_classes([IsAuthenticated])
def api_dashboard(request):
    """Endpoint para obtener datos del dashboard segÃºn el rol del usuario"""
    user = request.user
    data = {}
    menu = []
    
    # Generar menÃº segÃºn el rol del usuario
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
            
    elif rol_nombre == 'Medico':
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
            
        except Medico.DoesNotExist:
            return Response({'error': 'Perfil de mÃ©dico no encontrado'}, status=404)
            
    elif rol_nombre == 'Admision':
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
        
    elif rol_nombre == 'Administrador':
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
                        'nombre': 'DistribuciÃ³n de Citas',
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
                        'nombre': 'AdmisiÃ³n',
                        'icono': 'fa-clipboard-list',
                        'ruta': '/administrador/analisis-origen/admision/'
                    },
                    {
                        'nombre': 'DerivaciÃ³n',
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
                'nombre': 'AnÃ¡lisis por MÃ©dico',
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
                        'nombre': 'SatisfacciÃ³n',
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
            }
        ]
    
    # Incluir menÃº en la respuesta para todos los roles
    data['menu'] = menu
    
    return Response(data)

# -------------------
# Vistas para tendencias de citas
# -------------------

@login_required
def tendencias_citas(request):
    """
    Vista para la pÃ¡gina de anÃ¡lisis de tendencias de citas
    """
    # Verificar permisos del usuario
    if not es_recepcionista(request.user) and not es_administrador(request.user):
        return redirect('inicio')
    # Verificar si el rol es Admin o Administrador y ajustar
    rol_nombre = user.rol.nombre
    es_administrador = rol_nombre in ['Admin', 'Administrador', 'admin', 'administrador']
    
    # Generar menÃƒÂº segÃƒÂºn el rol
    rol_nombre = user.rol.nombre
    if rol_nombre == 'Paciente':
        # Datos especÃƒÂ­ficos para pacientes
        try:
            paciente = user.paciente
            
            # PrÃƒÂ³ximas citas
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
            
            # Notificaciones no leÃƒÂ­das
            notificaciones = Notificacion.objects.filter(
                usuario=user,
                leido=False
            ).count()
            
            data['notificaciones_no_leidas'] = notificaciones
            
            # MenÃƒÂº para pacientes
            menu = [
                {'nombre': 'Mis Citas', 'icono': 'fa-calendar-check', 'ruta': '/mis-citas/'},
                {'nombre': 'Reservar Cita', 'icono': 'fa-calendar-plus', 'ruta': '/reservar-cita/'},
                {'nombre': 'Historial MÃƒÂ©dico', 'icono': 'fa-file-medical-alt', 'ruta': '/mi-historial-medico/'},
                {'nombre': 'Mis Tratamientos', 'icono': 'fa-clipboard-list', 'ruta': '/mis-tratamientos/'},
                {'nombre': 'Mis Derivaciones', 'icono': 'fa-exchange-alt', 'ruta': '/derivaciones/'},
                {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/paciente/'},
                {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
            ]
            
        except Paciente.DoesNotExist:
            return Response({'error': 'Perfil de paciente no encontrado'}, status=404)
            
    elif user.rol.nombre == 'Medico':
        # Datos especÃƒÂ­ficos para mÃƒÂ©dicos
        try:
            medico = user.medico
            
            # Citas del dÃƒÂ­a
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
            
            # Notificaciones no leÃƒÂ­das
            notificaciones = Notificacion.objects.filter(
                usuario=user,
                leido=False
            ).count()
            
            data['notificaciones_no_leidas'] = notificaciones
            
            # MenÃƒÂº para mÃƒÂ©dicos
            menu = [
                {'nombre': 'Mi Agenda', 'icono': 'fa-calendar-alt', 'ruta': '/agenda/'},
                {'nombre': 'GestiÃƒÂ³n de Citas', 'icono': 'fa-calendar-week', 'ruta': '/gestion-citas/'},
                {'nombre': 'Atender Pacientes', 'icono': 'fa-stethoscope', 'ruta': '/atencion/'},
                {'nombre': 'Gestionar Horario', 'icono': 'fa-clock', 'ruta': '/disponibilidad/'},
                {'nombre': 'Historial MÃƒÂ©dico', 'icono': 'fa-file-medical', 'ruta': '/historial-medico/'},
                {'nombre': 'Derivar a Especialista', 'icono': 'fa-share', 'ruta': '/derivaciones/'},
                {'nombre': 'Programar Seguimientos', 'icono': 'fa-tasks', 'ruta': '/seguimientos/'},
                {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/medico/'},
                {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
            ]
            
            # Incluir menÃƒÂº en la respuesta
            data['menu'] = menu
            
        except Medico.DoesNotExist:
            return Response({'error': 'Perfil de mÃƒÂ©dico no encontrado'}, status=404)
            
    elif user.rol.nombre == 'Admision':
        # Datos especÃƒÂ­ficos para personal de admisiÃƒÂ³n
        # Citas del dÃƒÂ­a
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
        
        # Notificaciones no leÃƒÂ­das
        notificaciones = Notificacion.objects.filter(
            usuario=user,
            leido=False
        ).count()
        
        data['notificaciones_no_leidas'] = notificaciones
        
        # MenÃƒÂº para personal de admisiÃƒÂ³n
        menu = [
            {'nombre': 'Registrar Cita', 'icono': 'fa-calendar-plus', 'ruta': '/citas/crear/'},
            {'nombre': 'Buscar Paciente', 'icono': 'fa-search', 'ruta': '/buscar-paciente/'},
            {'nombre': 'Disponibilidad MÃƒÂ©dica', 'icono': 'fa-clipboard-check', 'ruta': '/disponibilidad/'},
            {'nombre': 'Justificar Inasistencia', 'icono': 'fa-exclamation-triangle', 'ruta': '/inasistencias/'},
            {'nombre': 'Mi Perfil', 'icono': 'fa-user', 'ruta': '/perfil/admision/'},
            {'nombre': 'Notificaciones', 'icono': 'fa-bell', 'ruta': '/notificaciones/'}
        ]
        
        # Incluir menÃƒÂº en la respuesta
        data['menu'] = menu
        
    elif user.rol.nombre == 'Administrador':
        # Datos especÃƒÂ­ficos para administradores
        # EstadÃƒÂ­sticas generales
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
        
        # Notificaciones no leÃƒÂ­das
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
                        'nombre': 'DistribuciÃ³n de Citas',
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
                        'nombre': 'AdmisiÃ³n',
                        'icono': 'fa-clipboard-list',
                        'ruta': '/administrador/analisis-origen/admision/'
                    },
                    {
                        'nombre': 'DerivaciÃ³n',
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
                'nombre': 'AnÃ¡lisis por MÃ©dico',
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
                        'nombre': 'SatisfacciÃ³n',
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
                'nombre': 'Historial MÃƒÂ©dico',
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
            }
        ]
        
    # Incluir menÃº en la respuesta para todos los roles
    data['menu'] = menu
    
    return Response(data)


# APIs para notificaciones

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_notificacion_leida(request):
    """Marca una notificaciÃƒÂ³n como leÃƒÂ­da"""
    try:
        data = json.loads(request.body)
        notificacion_id = data.get('notificacion_id')
        
        if not notificacion_id:
            return JsonResponse({'error': 'ID de notificaciÃ³n requerido'}, status=400)
        
        notificacion = get_object_or_404(Notificacion, 
id=notificacion_id, usuario=request.user)
        notificacion.leido = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        
        return JsonResponse({'success': True, 'message': 'NotificaciÃ³nmarcada como leÃƒda'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contador_notificaciones(request):
    """Devuelve el nÃƒÂºmero de notificaciones no leÃƒÂ­das del usuario"""
    try:
        no_leidas = Notificacion.objects.filter(usuario=request.user, 
leido=False).count()
        return JsonResponse({'success': True, 'no_leidas': no_leidas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


# Vistas para reportes y anÃ¡lisis estadÃ­sticos

@login_required
def comparativas_citas(request):
    """Vista para la pÃ¡gina de comparativas de citas"""
    # Verificar que el usuario tenga rol de administrador
    if not request.user.rol or request.user.rol.nombre != 'Administrador':
        messages.error(request, 'No tienes permisos para acceder a esta pÃ¡gina')
        return redirect('dashboard_view')
    
    # Obtener todas las especialidades para el filtro
    especialidades = Especialidad.objects.all().order_by('nombre')
    
    # Configurar fechas predeterminadas (mes actual)
    hoy = timezone.now().date()
    primer_dia_mes = hoy.replace(day=1)
    ultimo_dia_mes = (primer_dia_mes + timedelta(days=32)).replace(day=1) - timedelta(days=1)
    
    # InformaciÃ³n para el menÃº lateral y panel de administrador
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
        
        # Datos para el menÃº lateral y dashboard
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
    API para entregar datos comparativos de citas entre dos perÃ­odos.
    TambiÃ©n puede incluir dimensiones adicionales de anÃ¡lisis como: especialidad, dÃ­a de la semana y horario.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    try:
        # Verificar que el usuario tenga rol de administrador
        if not request.user.rol or request.user.rol.nombre != 'Administrador':
            logger.warning(f"Acceso denegado: Usuario {request.user.username} no tiene rol de Administrador")
            return JsonResponse({'error': 'No tienes permisos para acceder a esta informaciÃ³n', 'status': 'error'}, status=403)
            
        # Preparar logger para seguimiento detallado
        logger.info("API comparativa_citas - Iniciando procesamiento")
    
        # Log de parÃ¡metros recibidos en la peticiÃ³n
        logger.info(f"API comparativa_citas - ParÃ¡metros recibidos: {request.GET}")
        
        # Obtener parÃ¡metros de filtro para el primer perÃ­odo
        periodo1 = request.GET.get('periodo1', 'mensual')
        fecha_inicio1 = request.GET.get('fecha_inicio1')
        fecha_fin1 = request.GET.get('fecha_fin1')
        
        # Obtener parÃ¡metros de filtro para el segundo perÃ­odo
        periodo2 = request.GET.get('periodo2', 'mensual')
        fecha_inicio2 = request.GET.get('fecha_inicio2')
        fecha_fin2 = request.GET.get('fecha_fin2')
        
        # Filtros comunes
        especialidad_id = request.GET.get('especialidad', '')
        medico_id = request.GET.get('medico', '')
        
        # Verificar si se solicitan dimensiones adicionales
        incluir_dimensiones = request.GET.get('incluir_dimensiones') == 'true'
        
        logger.info(f"ParÃ¡metros procesados: periodo1={periodo1}, fecha_inicio1={fecha_inicio1}, fecha_fin1={fecha_fin1}, periodo2={periodo2}, fecha_inicio2={fecha_inicio2}, fecha_fin2={fecha_fin2}, especialidad={especialidad_id}, medico={medico_id}, incluir_dimensiones={incluir_dimensiones}")
        
        # Convertir fechas a objetos date
        fecha_inicio1 = datetime.strptime(fecha_inicio1, '%Y-%m-%d').date() if fecha_inicio1 else None
        fecha_fin1 = datetime.strptime(fecha_fin1, '%Y-%m-%d').date() if fecha_fin1 else None
        fecha_inicio2 = datetime.strptime(fecha_inicio2, '%Y-%m-%d').date() if fecha_inicio2 else None
        fecha_fin2 = datetime.strptime(fecha_fin2, '%Y-%m-%d').date() if fecha_fin2 else None
        
        # FunciÃ³n para obtener datos de citas segÃºn filtros
        def obtener_datos_periodo(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            import logging
            logger = logging.getLogger(__name__)
            
            # Log de parÃ¡metros recibidos
            logger.info(f"obtener_datos_periodo - ParÃ¡metros: fecha_inicio={fecha_inicio}, fecha_fin={fecha_fin}, especialidad_id={especialidad_id}, medico_id={medico_id}")
            
            # Consulta base para citas
            query = Cita.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            logger.info(f"Citas encontradas en rango de fechas: {query.count()}")
            
            # Aplicar filtros adicionales si se proporcionan y son vÃ¡lidos
            # Si especialidad_id es '0' o 'Todas', no aplicar filtro (mostrar todas)
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                query = query.filter(medico__especialidad_id=especialidad_id)
                logger.info(f"Aplicando filtro de especialidad {especialidad_id}, citas restantes: {query.count()}")
            else:
                logger.info(f"No se aplica filtro de especialidad, valor recibido: {especialidad_id}")
            
            # Si medico_id es '0' o 'Todos', no aplicar filtro (mostrar todos)
            if medico_id and medico_id not in ['0', 'Todos'] and medico_id.isdigit():
                query = query.filter(medico__id=medico_id)  # Corregido: medico__id en lugar de medico_id
                logger.info(f"Aplicando filtro de mÃ©dico {medico_id}, citas restantes: {query.count()}")
            else:
                logger.info(f"No se aplica filtro de mÃ©dico, valor recibido: {medico_id}")
            
            # Contar citas por estado (usando los nombres exactos de la base de datos, en minÃºsculas)
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
        
        # FunciÃ³n para obtener datos por especialidad
        def obtener_datos_especialidades(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            logger.info(f"Obteniendo datos por especialidad: periodo {fecha_inicio} - {fecha_fin}")
            
            # Si se ha seleccionado una especialidad especÃ­fica, no tiene sentido mostrar la comparativa por especialidades
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                logger.info(f"Se ha seleccionado una especialidad especÃ­fica ({especialidad_id}), no se muestra comparativa por especialidades")
                return []
            
            # En lugar de buscar a travÃ©s de la relaciÃ³n inversa compleja, primero obtenemos todos los mÃ©dicos con citas
            # y luego obtenemos sus especialidades
            ids_medicos_con_citas = Cita.objects.filter(
                fecha__gte=fecha_inicio,
                fecha__lte=fecha_fin
            ).values_list('medico', flat=True).distinct()
            
            # Ahora obtenemos las especialidades de esos mÃ©dicos
            especialidades = Especialidad.objects.filter(
                medicos__id__in=ids_medicos_con_citas
            ).distinct()
            
            logger.info(f"Encontradas {especialidades.count()} especialidades con citas en el perÃ­odo")
            
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
        
        # FunciÃ³n para obtener datos por dÃ­a de la semana
        def obtener_datos_dias_semana(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            logger.info(f"Obteniendo datos por dÃ­a de la semana: periodo {fecha_inicio} - {fecha_fin}")
            
            dias_semana = {
                'lunes': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'martes': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'miÃ©rcoles': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'jueves': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'viernes': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'sÃ¡bado': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'domingo': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0}
            }
            
            # Obtener todas las citas en el perÃ­odo
            query = Cita.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            
            # Aplicar filtros adicionales si se proporcionan y son vÃ¡lidos
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                query = query.filter(medico__especialidad_id=especialidad_id)
            
            if medico_id and medico_id not in ['0', 'Todos'] and medico_id.isdigit():
                query = query.filter(medico__id=medico_id)  # Corregido: medico__id en lugar de medico_id
            
            logger.info(f"Analizando {query.count()} citas para datos por dÃ­a de la semana")
            
            # Para cada cita, incrementar el contador correspondiente
            for cita in query:
                # Convertir nÃºmero de dÃ­a de semana (0-6, donde 0 es lunes) a nombre
                nombres_dias = ['lunes', 'martes', 'miÃ©rcoles', 'jueves', 'viernes', 'sÃ¡bado', 'domingo']
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
        
        # FunciÃ³n para obtener datos por horario (maÃ±ana vs tarde)
        def obtener_datos_horarios(fecha_inicio, fecha_fin, especialidad_id, medico_id):
            logger.info(f"Obteniendo datos por horario: periodo {fecha_inicio} - {fecha_fin}")
            
            # Definir horarios (12:00 como lÃ­mite entre maÃ±ana y tarde)
            horarios = {
                'maÃ±ana': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0},
                'tarde': {'pendientes': 0, 'confirmadas': 0, 'atendidas': 0, 'canceladas': 0, 'total': 0}
            }
            
            # Obtener todas las citas en el perÃ­odo
            query = Cita.objects.filter(fecha__gte=fecha_inicio, fecha__lte=fecha_fin)
            
            # Aplicar filtros adicionales si se proporcionan y son vÃ¡lidos
            if especialidad_id and especialidad_id not in ['0', 'Todas'] and especialidad_id.isdigit():
                query = query.filter(medico__especialidad_id=especialidad_id)
            
            if medico_id and medico_id not in ['0', 'Todos'] and medico_id.isdigit():
                query = query.filter(medico__id=medico_id)  # Corregido: medico__id en lugar de medico_id
            
            logger.info(f"Analizando {query.count()} citas para datos por horario")
            
            # Para cada cita, incrementar el contador correspondiente
            for cita in query:
                # Determinar si es maÃ±ana o tarde basado en la hora_inicio
                horario = 'maÃ±ana' if cita.hora_inicio.hour < 12 else 'tarde'
                
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
        
        # Obtener datos para ambos perÃ­odos
        datos_periodo1 = obtener_datos_periodo(fecha_inicio1, fecha_fin1, especialidad_id, medico_id)
        datos_periodo2 = obtener_datos_periodo(fecha_inicio2, fecha_fin2, especialidad_id, medico_id)
        
        # Calcular variaciones entre perÃ­odos
        variaciones = {
            'total': datos_periodo2['total'] - datos_periodo1['total'],
            'pendientes': datos_periodo2['pendientes'] - datos_periodo1['pendientes'],
            'confirmadas': datos_periodo2['confirmadas'] - datos_periodo1['confirmadas'],
            'atendidas': datos_periodo2['atendidas'] - datos_periodo1['atendidas'],
            'canceladas': datos_periodo2['canceladas'] - datos_periodo1['canceladas'],
            'porcentaje_asistencia': datos_periodo2['porcentaje_asistencia'] - datos_periodo1['porcentaje_asistencia']
        }
        
        # ValidaciÃ³n exhaustiva de datos para evitar errores
        for periodo in [datos_periodo1, datos_periodo2]:
            # Verificar y establecer valores predeterminados para todos los campos necesarios
            campos_requeridos = ['pendientes', 'confirmadas', 'atendidas', 'canceladas', 'total', 'porcentaje_asistencia']
            for key in campos_requeridos:
                if key not in periodo or periodo[key] is None:
                    logger.warning(f"Campo {key} faltante o nulo en datos del perÃ­odo, estableciendo a 0")
                    periodo[key] = 0
                    
            # VerificaciÃ³n adicional del porcentaje de asistencia
            if periodo['total'] > 0:
                # Recalcular porcentaje de asistencia por si acaso
                periodo['porcentaje_asistencia'] = round((periodo['atendidas'] / periodo['total']) * 100, 2)
            else:
                periodo['porcentaje_asistencia'] = 0
                
            logger.info(f"Datos del perÃ­odo validados: {periodo}")

        # Registrar en el log las variaciones calculadas
        logger.info(f"Variaciones calculadas entre periodos: {variaciones}")
        
        # Calcular variaciones porcentuales
        variaciones_porcentuales = {}
        for key, value in variaciones.items():
            # Si es el porcentaje de asistencia, solo copiar el valor de la variaciÃ³n
            if key == 'porcentaje_asistencia':
                variaciones_porcentuales[key] = round(value, 2)
            # Para los demÃ¡s, calcular la variaciÃ³n porcentual si hay datos en el primer perÃ­odo
            elif datos_periodo1[key] > 0:
                variaciones_porcentuales[key] = round((value / datos_periodo1[key]) * 100, 2)
            # Si no hay datos en el primer perÃ­odo pero hay una variaciÃ³n, ponerla como 100%
            elif value > 0:
                variaciones_porcentuales[key] = 100.0
            # Si no hay datos en ninguno de los perÃ­odos, la variaciÃ³n es 0
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
            logger.info(f"API comparativa_citas - Devolviendo datos con Ã©xito: {datos_periodo1['total']} citas en periodo 1, {datos_periodo2['total']} citas en periodo 2")
        else:
            # No hay datos, pero aun asÃ­ devolver una estructura vÃ¡lida para evitar errores en el frontend
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
                'message': 'No se encontraron citas para los perÃ­odos y filtros seleccionados'
            }
            logger.warning(f"API comparativa_citas - No se encontraron citas para los filtros seleccionados")
        
        # Agregar dimensiones adicionales si se solicitan
        if incluir_dimensiones:
            logger.info("Se solicitaron dimensiones adicionales, procesando datos...")
            
            # Combinar datos de ambos perÃ­odos para las dimensiones adicionales
            # (Usar el rango de fechas mÃ¡s amplio entre los dos perÃ­odos)
            fecha_inicio_combinada = min(fecha_inicio1, fecha_inicio2)
            fecha_fin_combinada = max(fecha_fin1, fecha_fin2)
            
            logger.info(f"Rango combinado para dimensiones adicionales: {fecha_inicio_combinada} - {fecha_fin_combinada}")
            
            # Obtener datos para las diferentes dimensiones
            datos_especialidades = obtener_datos_especialidades(fecha_inicio_combinada, fecha_fin_combinada, especialidad_id, medico_id)
            datos_dias_semana = obtener_datos_dias_semana(fecha_inicio_combinada, fecha_fin_combinada, especialidad_id, medico_id)
            datos_horarios = obtener_datos_horarios(fecha_inicio_combinada, fecha_fin_combinada, especialidad_id, medico_id)
            
            # AÃ±adir datos a la respuesta
            response['dimensiones_adicionales'] = {
                'especialidades': datos_especialidades,
                'dias_semana': datos_dias_semana,
                'horarios': datos_horarios
            }
            
            logger.info(f"Datos de dimensiones adicionales agregados: {len(datos_especialidades)} especialidades, {len(datos_dias_semana)} dÃ­as, {len(datos_horarios)} horarios")
        
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
        
        # Devolver una respuesta con estructura segura que no causarÃ¡ errores en el frontend
        # Generamos una respuesta mÃ­nima pero vÃ¡lida que el frontend puede manejar
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
            'message': 'OcurriÃ³ un error al procesar los datos. Se muestran datos vacÃ­os como respaldo.'
        }, status=200)  # Devolver 200 en lugar de 500 para que el frontend aÃºn lo muestre


@login_required
def api_medicos_por_especialidad(request):
    """
    API endpoint para obtener mÃ©dicos filtrados por especialidad.
    """
    import logging
    logger = logging.getLogger(__name__)
    
    # Obtener el ID de la especialidad de la peticiÃ³n
    especialidad_id = request.GET.get('especialidad_id', '0')
    logger.info(f"API medicos_por_especialidad llamada con especialidad_id={especialidad_id}")
    
    # Lista para almacenar los mÃ©dicos
    medicos_lista = []
    
    try:
        # Si se seleccionÃ³ una especialidad especÃ­fica (diferente de 'Todas')
        if especialidad_id and especialidad_id != '0':
            # Consultar los mÃ©dicos que pertenecen a esa especialidad
            medicos = Medico.objects.filter(especialidad_id=especialidad_id)
            logger.info(f"Encontrados {medicos.count()} mÃ©dicos para la especialidad {especialidad_id}")
        else:
            # Si no se seleccionÃ³ especialidad o se seleccionÃ³ 'Todas', mostrar todos los mÃ©dicos
            medicos = Medico.objects.all()
            logger.info(f"Mostrando todos los mÃ©dicos: {medicos.count()} encontrados")
        
        # Formatear datos para el frontend
        for medico in medicos:
            nombre_completo = f"{medico.usuario.nombres} {medico.usuario.apellidos}"
            medico_data = {
                'id': medico.id,
                'nombre_completo': nombre_completo
            }
            medicos_lista.append(medico_data)
    
    except Exception as e:
        logger.error(f"Error al obtener mÃ©dicos: {str(e)}")
        return JsonResponse({'medicos': [], 'error': str(e), 'status': 'error'})
    
    # Devolver la lista de mÃ©dicos en formato JSON
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
    Vista para la pÃ¡gina de anÃ¡lisis de tasas de asistencia y recuperaciÃ³n
    """
    # Solo accesible para administradores
    if not request.user.rol or request.user.rol.nombre != 'Administrador':
        messages.error(request, 'No tiene permisos para acceder a esta secciÃ³n')
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
    API para obtener datos de tasas de asistencia y recuperaciÃ³n
    """
    try:
        # Obtener parÃ¡metros de la solicitud
        fecha_inicio = request.GET.get('fecha_inicio', None)
        fecha_fin = request.GET.get('fecha_fin', None)
        especialidad_id = request.GET.get('especialidad_id', '0')
        medico_id = request.GET.get('medico_id', '0')
        
        # Validar fechas
        if not fecha_inicio or not fecha_fin:
            # Si no se especifican fechas, usar Ãºltimos 3 meses
            fecha_fin = timezone.now().date()
            fecha_inicio = fecha_fin - timedelta(days=90)
        else:
            # Convertir strings a objetos date
            try:
                fecha_inicio = datetime.strptime(fecha_inicio, '%Y-%m-%d').date()
                fecha_fin = datetime.strptime(fecha_fin, '%Y-%m-%d').date()
            except ValueError:
                return Response({
                    'error': 'Formato de fecha invÃ¡lido. Use YYYY-MM-DD',
                    'status': 'error'
                }, status=400)
        
        # Construir filtro base para las citas
        filtro_citas = Q(fecha__gte=fecha_inicio) & Q(fecha__lte=fecha_fin)
        
        # Aplicar filtros adicionales si se especifican
        if especialidad_id and especialidad_id != '0':
            filtro_citas &= Q(medico__especialidad_id=especialidad_id)
        
        if medico_id and medico_id != '0':
            filtro_citas &= Q(medico_id=medico_id)
        
        # Obtener todas las citas segÃºn los filtros
        citas = Cita.objects.filter(filtro_citas)
        
        # Calcular mÃ©tricas bÃ¡sicas
        total_citas = citas.count()
        citas_atendidas = citas.filter(estado='atendida').count()
        citas_pendientes = citas.filter(estado='pendiente').count()
        citas_confirmadas = citas.filter(estado='confirmada').count()
        citas_canceladas = citas.filter(estado='cancelada').count()
        
        # CÃ¡lculo de tasas
        tasa_asistencia = (citas_atendidas / total_citas * 100) if total_citas > 0 else 0
        tasa_inasistencia = (citas_confirmadas / total_citas * 100) if total_citas > 0 else 0
        tasa_cancelacion = (citas_canceladas / total_citas * 100) if total_citas > 0 else 0
        
        # Calcular mÃ©tricas de recuperaciÃ³n de inasistencias
        # Identificar citas con inasistencia (confirmadas que no fueron atendidas)
        inasistencias = citas.filter(estado='confirmada', asistio=False)
        inasistencias_totales = inasistencias.count()
        
        # Identificar cuÃ¡ntas de estas inasistencias tienen citas de seguimiento que sÃ­ fueron atendidas
        inasistencias_recuperadas = 0
        for cita in inasistencias:
            # Verificar si esta cita tiene alguna cita de seguimiento que fue atendida
            if cita.citas_seguimiento.filter(estado='atendida').exists():
                inasistencias_recuperadas += 1
        
        # Calcular tasa de recuperaciÃ³n
        tasa_recuperacion = (inasistencias_recuperadas / inasistencias_totales * 100) if inasistencias_totales > 0 else 0
        
        # Calcular evoluciÃ³n mensual
        # Dividir el perÃ­odo en 6 intervalos para mostrar evoluciÃ³n
        dias_totales = (fecha_fin - fecha_inicio).days
        intervalo_dias = max(dias_totales // 6, 1)  # Al menos 1 dÃ­a por intervalo
        
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
            
            # Calcular tasa de recuperaciÃ³n del intervalo
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


