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

# Vistas públicas
def home(request):
    """Vista de la página de bienvenida"""
    return render(request, 'home.html')

def login_view(request):
    """Vista de inicio de sesión"""
    if request.method == 'POST':
        dni = request.POST.get('dni')
        password = request.POST.get('password')
        user = authenticate(request, username=dni, password=password)
        
        if user is not None:
            login(request, user)
            
            # Redirección según el rol del usuario
            if user.rol:
                if user.rol.nombre == 'Paciente':
                    return redirect('dashboard_paciente')
                elif user.rol.nombre == 'Médico':
                    return redirect('dashboard_medico')
                elif user.rol.nombre == 'Admisión':
                    return redirect('dashboard_admision')
                elif user.rol.nombre == 'Administrador':
                    return redirect('dashboard_admin')
            
            # Si no tiene rol asignado, redirigir a la página principal
            return redirect('home')
        else:
            messages.error(request, 'DNI o contraseña incorrectos')
    
    return render(request, 'auth/login.html')

def registro_view(request):
    """Vista de registro de usuarios con selección de rol"""
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
            
            # Crear perfil según el rol
            if rol_nombre == 'Paciente':
                Paciente.objects.create(usuario=user)
            elif rol_nombre == 'Medico':
                # Para médicos, usar la especialidad seleccionada o una por defecto
                from .models import Medico
                especialidad_id = request.POST.get('especialidad')
                
                try:
                    if especialidad_id and especialidad_id.isdigit():
                        especialidad = Especialidad.objects.get(id=especialidad_id)
                    else:
                        # Si no se seleccionó especialidad, usar General como predeterminada
                        especialidad, _ = Especialidad.objects.get_or_create(nombre='General')
                except Especialidad.DoesNotExist:
                    especialidad, _ = Especialidad.objects.get_or_create(nombre='General')
                
                # Asignar un CMP provisional que se actualizará después
                cmp_provisional = f"TEMP-{user.dni}"
                Medico.objects.create(usuario=user, especialidad=especialidad, cmp=cmp_provisional)
            
            # Iniciar sesión automáticamente
            login(request, user)
            messages.success(request, f'¡Registro exitoso como {rol_nombre}! Bienvenido al sistema.')
            
            # Redireccionar según el rol
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
    """Cerrar sesión"""
    logout(request)
    return redirect('home')

# Vistas protegidas por rol
@login_required
def dashboard_view(request):
    """Redirecciona al dashboard específico según el rol del usuario"""
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
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        paciente = request.user.paciente
        
        # Obtener próximas citas
        proximas_citas = Cita.objects.filter(
            paciente=paciente,
            fecha__gte=timezone.now().date(),
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora_inicio')[:5]
        
        # Obtener historial médico
        historial = HistorialMedico.objects.filter(paciente=paciente).order_by('-fecha')[:5]
        
        # Obtener derivaciones activas
        derivaciones = Derivacion.objects.filter(
            paciente=paciente,
            estado='pendiente',
            fecha_derivacion__gte=timezone.now().date() - timedelta(days=30)
        )
        
        # Obtener notificaciones no leídas
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
        messages.error(request, 'No se encontró el perfil de paciente')
        return redirect('home')

@login_required
def dashboard_medico(request):
    """Dashboard para médicos"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Medico':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    try:
        medico = request.user.medico
        
        # Obtener citas del día
        hoy = timezone.now().date()
        citas_hoy = Cita.objects.filter(
            medico=medico,
            fecha=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('hora_inicio')
        
        # Obtener próximas citas (excluyendo hoy)
        proximas_citas = Cita.objects.filter(
            medico=medico,
            fecha__gt=hoy,
            estado__in=['pendiente', 'confirmada']
        ).order_by('fecha', 'hora_inicio')[:10]
        
        # Obtener derivaciones realizadas recientemente
        derivaciones = Derivacion.objects.filter(
            medico_origen=medico
        ).order_by('-fecha_derivacion')[:5]
        
        # Obtener notificaciones no leídas
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
        messages.error(request, 'No se encontró el perfil de médico')
        return redirect('home')

@login_required
def dashboard_admision(request):
    """Dashboard para personal de admisión"""
    # Verificar que el usuario tenga el rol correcto
    if not request.user.rol or request.user.rol.nombre != 'Admision':
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    # Obtener citas del día
    hoy = timezone.now().date()
    citas_hoy = Cita.objects.filter(
        fecha=hoy,
        estado__in=['pendiente', 'confirmada']
    ).order_by('hora_inicio')
    
    # Obtener pacientes con faltas consecutivas
    pacientes_faltas = Paciente.objects.filter(faltas_consecutivas__gt=0).order_by('-faltas_consecutivas')
    
    # Obtener notificaciones no leídas
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
        messages.error(request, 'No tienes permiso para acceder a esta página')
        return redirect('home')
    
    # Estadísticas generales
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_citas = Cita.objects.count()
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    citas_atendidas = Cita.objects.filter(estado='atendida').count()
    
    # Citas por especialidad
    citas_por_especialidad = Cita.objects.values('medico__especialidad__nombre').annotate(
        total=Count('id')
    ).order_by('-total')[:5]
    
    # Obtener notificaciones no leídas
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
    
    # Verificar rol del usuario
    if not user.rol:
        return Response({'error': 'Usuario sin rol asignado'}, status=400)
    
    # Generar menú según el rol
    if user.rol.nombre == 'Paciente':
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
                {'nombre': 'Mis Citas', 'icono': '📅', 'ruta': '/mis-citas/'},
                {'nombre': 'Reservar Cita', 'icono': '📝', 'ruta': '/citas/reservar/'},
                {'nombre': 'Historial Médico', 'icono': '📖', 'ruta': '/historial/'},
                {'nombre': 'Mis Derivaciones', 'icono': '📤', 'ruta': '/derivaciones/'},
                {'nombre': 'Notificaciones', 'icono': '🔔', 'ruta': '/notificaciones/'},
                {'nombre': 'Perfil', 'icono': '👤', 'ruta': '/perfil/'}
            ]
            
        except Paciente.DoesNotExist:
            return Response({'error': 'Perfil de paciente no encontrado'}, status=404)
            
    elif user.rol.nombre == 'Medico':
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
                {'nombre': 'Mi Agenda', 'icono': '📅', 'ruta': '/agenda/'},
                {'nombre': 'Atender Pacientes', 'icono': '🩺', 'ruta': '/atencion/'},
                {'nombre': 'Gestionar Horario', 'icono': '⏰', 'ruta': '/disponibilidad/'},
                {'nombre': 'Historial Médico', 'icono': '📚', 'ruta': '/historial-medico/'},
                {'nombre': 'Derivar a Especialista', 'icono': '➡️', 'ruta': '/derivaciones/'},
                {'nombre': 'Programar Seguimientos', 'icono': '📌', 'ruta': '/seguimientos/'},
                {'nombre': 'Notificaciones', 'icono': '🔔', 'ruta': '/notificaciones/'}
            ]
            
            # Incluir menú en la respuesta
            data['menu'] = menu
            
        except Medico.DoesNotExist:
            return Response({'error': 'Perfil de médico no encontrado'}, status=404)
            
    elif user.rol.nombre == 'Admision':
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
            {'nombre': 'Registrar Cita', 'icono': '📝', 'ruta': '/citas/crear/'},
            {'nombre': 'Buscar Paciente', 'icono': '🔍', 'ruta': '/buscar-paciente/'},
            {'nombre': 'Disponibilidad Médica', 'icono': '📋', 'ruta': '/disponibilidad/'},
            {'nombre': 'Justificar Inasistencia', 'icono': '⚠️', 'ruta': '/inasistencias/'},
            {'nombre': 'Notificaciones', 'icono': '🔔', 'ruta': '/notificaciones/'}
        ]
        
        # Incluir menú en la respuesta
        data['menu'] = menu
        
    elif user.rol.nombre == 'Administrador':
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
        
        # Menú para administradores
        menu = [
            {'nombre': 'Estadísticas Generales', 'icono': '📊', 'ruta': '/reportes/estadisticas/'},
            {'nombre': 'Citas por Especialidad', 'icono': '📈', 'ruta': '/reportes/especialidades/'},
            {'nombre': 'Control de Inasistencias', 'icono': '🚫', 'ruta': '/reportes/inasistencias/'},
            {'nombre': 'Usuarios del Sistema', 'icono': '👥', 'ruta': '/usuarios/'},
            {'nombre': 'Notificaciones', 'icono': '🔔', 'ruta': '/notificaciones/'}
        ]
    
    # Incluir menú en la respuesta
    data['menu'] = menu
    
    return Response(data)


# APIs para notificaciones

@api_view(['POST'])
@permission_classes([IsAuthenticated])
def marcar_notificacion_leida(request):
    """Marca una notificación como leída"""
    try:
        data = json.loads(request.body)
        notificacion_id = data.get('notificacion_id')
        
        if not notificacion_id:
            return JsonResponse({'error': 'ID de notificación requerido'}, status=400)
        
        notificacion = get_object_or_404(Notificacion, id=notificacion_id, usuario=request.user)
        notificacion.leido = True
        notificacion.fecha_lectura = timezone.now()
        notificacion.save()
        
        return JsonResponse({'success': True, 'message': 'Notificación marcada como leída'})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def contador_notificaciones(request):
    """Devuelve el número de notificaciones no leídas del usuario"""
    try:
        no_leidas = Notificacion.objects.filter(usuario=request.user, leido=False).count()
        return JsonResponse({'success': True, 'no_leidas': no_leidas})
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=500)
