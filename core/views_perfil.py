from django.shortcuts import render, redirect, get_object_or_404
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from datetime import timedelta
from django.http import HttpResponseForbidden
from PIL import Image
from io import BytesIO
from django.core.files.uploadedfile import InMemoryUploadedFile
import sys
from .models import Usuario, Paciente, Medico, Cita, HistorialMedico, Derivacion

@login_required
def perfil_usuario(request, usuario_id=None, tipo=None):
    """
    Vista unificada para mostrar el perfil de cualquier usuario.
    
    Parámetros:
    - usuario_id: ID del usuario a mostrar (si es None, muestra el perfil del usuario actual)
    - tipo: Tipo de perfil a mostrar ('paciente' o 'medico')
    
    Si no se proporciona tipo, se determina automáticamente según el rol del usuario.
    """
    user = request.user
    
    # Determinar el tipo de perfil si no se proporciona
    if tipo is None:
        if hasattr(user, 'paciente'):
            tipo = 'paciente'
        elif hasattr(user, 'medico'):
            tipo = 'medico'
        elif user.rol and user.rol.nombre == 'Admision':
            tipo = 'admision'
        elif user.rol and user.rol.nombre == 'Administrador':
            tipo = 'admin'
        else:
            messages.error(request, "No se pudo determinar el tipo de perfil para tu usuario.")
            return redirect('dashboard')
    
    # Verificar permisos y obtener el usuario a mostrar
    if usuario_id is None:
        # Mostrar perfil propio
        if tipo == 'paciente' and not hasattr(user, 'paciente'):
            messages.error(request, "No tienes un perfil de paciente en el sistema.")
            return redirect('dashboard')
        elif tipo == 'medico' and not hasattr(user, 'medico'):
            messages.error(request, "No tienes un perfil de médico en el sistema.")
            return redirect('dashboard')
        elif tipo == 'admision' and (not user.rol or user.rol.nombre != 'Admision'):
            messages.error(request, "No tienes un perfil de admisión en el sistema.")
            return redirect('dashboard')
        elif tipo == 'admin' and (not user.rol or user.rol.nombre != 'Administrador'):
            messages.error(request, "No tienes un perfil de administrador en el sistema.")
            return redirect('dashboard')
        
        usuario = user
        es_propio = True
    else:
        # Mostrar perfil de otro usuario
        usuario = get_object_or_404(Usuario, id=usuario_id)
        
        # Verificar permisos
        if tipo == 'paciente':
            if not (hasattr(user, 'medico') or 
                    user.rol and user.rol.nombre in ['Admision', 'Administrador']):
                messages.error(request, "No tienes permisos para ver este perfil de paciente.")
                return redirect('dashboard')
            
            if not hasattr(usuario, 'paciente'):
                messages.error(request, "El usuario seleccionado no tiene un perfil de paciente.")
                return redirect('dashboard')
                
        elif tipo == 'medico':
            if not (user.rol and user.rol.nombre in ['Administrador']):
                messages.error(request, "No tienes permisos para ver este perfil de médico.")
                return redirect('dashboard')
            
            if not hasattr(usuario, 'medico'):
                messages.error(request, "El usuario seleccionado no tiene un perfil de médico.")
                return redirect('dashboard')
        
        es_propio = (usuario.id == user.id)
    
    # Preparar datos comunes
    datos = {
        'usuario': usuario,
        'es_propio': es_propio,
    }
    
    # Preparar datos específicos según el tipo de perfil
    if tipo == 'paciente':
        datos.update(obtener_datos_paciente(usuario))
        template = 'paciente/perfil.html'
    elif tipo == 'medico':
        datos.update(obtener_datos_medico(usuario))
        template = 'medico/perfil.html'
    elif tipo == 'admision':
        datos.update(obtener_datos_admision(usuario))
        template = 'admision/perfil.html'
    elif tipo == 'admin':
        datos.update(obtener_datos_admin(usuario))
        template = 'admin/perfil.html'
    
    # Renderizar plantilla
    return render(request, template, datos)

def obtener_datos_paciente(usuario):
    """Obtiene los datos específicos para el perfil de un paciente."""
    paciente = usuario.paciente
    
    # Obtener estadísticas
    total_citas = Cita.objects.filter(paciente=paciente).count()
    citas_pendientes = Cita.objects.filter(
        paciente=paciente,
        fecha__gte=timezone.now().date(),
        estado__in=['pendiente', 'confirmada']
    ).count()
    citas_completadas = Cita.objects.filter(
        paciente=paciente,
        estado='atendida'
    ).count()
    
    # Obtener historial médico
    historial = HistorialMedico.objects.filter(paciente=paciente).order_by('-fecha')[:5]
    
    # Obtener derivaciones activas
    derivaciones_activas = Derivacion.objects.filter(
        paciente=paciente,
        estado='pendiente',
        fecha_derivacion__gte=timezone.now().date() - timezone.timedelta(days=365)  # Último año
    ).order_by('-fecha_derivacion')
    
    # Obtener próximas citas
    proximas_citas = Cita.objects.filter(
        paciente=paciente,
        fecha__gte=timezone.now().date(),
        estado__in=['pendiente', 'confirmada']
    ).order_by('fecha', 'hora_inicio')[:5]
    
    return {
        'paciente': paciente,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_completadas': citas_completadas,
        'historial': historial,
        'derivaciones_activas': derivaciones_activas,
        'proximas_citas': proximas_citas
    }

def obtener_datos_medico(usuario):
    """Obtiene los datos específicos para el perfil de un médico."""
    medico = usuario.medico
    especialidad = medico.especialidad
    
    # Obtener estadísticas
    hoy = timezone.now().date()
    
    # Citas del día
    citas_hoy = Cita.objects.filter(
        medico=medico,
        fecha=hoy,
        estado__in=['pendiente', 'confirmada']
    ).count()
    
    # Próximas citas
    proximas_citas = Cita.objects.filter(
        medico=medico,
        fecha__gte=hoy,
        estado__in=['pendiente', 'confirmada']
    ).order_by('fecha', 'hora_inicio')[:5]
    
    # Citas totales atendidas
    citas_atendidas = Cita.objects.filter(
        medico=medico,
        estado='atendida'
    ).count()
    
    # Pacientes atendidos (únicos)
    pacientes_atendidos = Cita.objects.filter(
        medico=medico,
        estado='atendida'
    ).values('paciente').distinct().count()
    
    # Historial de atenciones recientes (usando las citas atendidas)
    citas_recientes = Cita.objects.filter(
        medico=medico,
        estado='atendida'
    ).order_by('-fecha')[:5]
    
    # Obtenemos los historiales médicos asociados a esas citas
    historiales_ids = []
    for cita in citas_recientes:
        # Buscamos si hay un historial médico para esta cita
        try:
            historial = HistorialMedico.objects.filter(
                paciente=cita.paciente,
                fecha__date=cita.fecha
            ).first()
            if historial and historial.id not in historiales_ids:
                historiales_ids.append(historial.id)
        except Exception:
            pass
    
    historial_atenciones = HistorialMedico.objects.filter(id__in=historiales_ids).order_by('-fecha')
    
    return {
        'medico': medico,
        'especialidad': especialidad,
        'citas_hoy': citas_hoy,
        'proximas_citas': proximas_citas,
        'citas_atendidas': citas_atendidas,
        'pacientes_atendidos': pacientes_atendidos,
        'historial_atenciones': historial_atenciones
    }

def obtener_datos_admision(usuario):
    """Obtiene los datos específicos para el perfil de un usuario de admisión."""
    # Obtener estadísticas
    hoy = timezone.now().date()
    
    # Citas registradas hoy
    citas_registradas_hoy = Cita.objects.filter(
        fecha_creacion__date=hoy
    ).count()
    
    # Citas para hoy
    citas_hoy = Cita.objects.filter(
        fecha=hoy
    ).count()
    
    # Citas pendientes
    citas_pendientes = Cita.objects.filter(
        fecha__gte=hoy,
        estado='pendiente'
    ).count()
    
    # Últimas citas registradas
    ultimas_citas = Cita.objects.all().order_by('-fecha_creacion')[:10]
    
    return {
        'citas_registradas_hoy': citas_registradas_hoy,
        'citas_hoy': citas_hoy,
        'citas_pendientes': citas_pendientes,
        'ultimas_citas': ultimas_citas
    }

def obtener_datos_admin(usuario):
    """Obtiene los datos específicos para el perfil de un administrador."""
    # Estadísticas generales
    total_pacientes = Paciente.objects.count()
    total_medicos = Medico.objects.count()
    total_citas = Cita.objects.count()
    
    # Estadísticas de citas
    citas_pendientes = Cita.objects.filter(estado='pendiente').count()
    citas_atendidas = Cita.objects.filter(estado='atendida').count()
    citas_canceladas = Cita.objects.filter(estado='cancelada').count()
    
    # Usuarios del sistema
    usuarios_sistema = Usuario.objects.all().count()
    
    # Actividad reciente (últimos usuarios registrados)
    ultimos_usuarios = Usuario.objects.all().order_by('-date_joined')[:5]
    
    return {
        'total_pacientes': total_pacientes,
        'total_medicos': total_medicos,
        'total_citas': total_citas,
        'citas_pendientes': citas_pendientes,
        'citas_atendidas': citas_atendidas,
        'citas_canceladas': citas_canceladas,
        'usuarios_sistema': usuarios_sistema,
        'ultimos_usuarios': ultimos_usuarios
    }

@login_required
def subir_foto_perfil(request):
    """
    Vista para procesar la subida de una foto de perfil.
    Funciona tanto para pacientes como para médicos.
    Valida que la imagen sea PNG o JPG, no supere 1MB y la comprime antes de guardarla.
    """
    if request.method != 'POST':
        return redirect('perfil_usuario')
    
    # Determinar el tipo de usuario para la redirección
    if hasattr(request.user, 'paciente'):
        redirect_url = 'perfil_paciente'
        kwargs = {}
    elif hasattr(request.user, 'medico'):
        redirect_url = 'perfil_medico'
        kwargs = {}
    elif request.user.rol and request.user.rol.nombre == 'Admision':
        redirect_url = 'perfil_admision'
        kwargs = {}
    elif request.user.rol and request.user.rol.nombre == 'Administrador':
        redirect_url = 'perfil_admin'
        kwargs = {}
    else:
        messages.error(request, "No se pudo determinar el tipo de perfil para tu usuario.")
        return redirect('dashboard')
    
    # Procesar la imagen
    if 'foto_perfil' in request.FILES:
        foto = request.FILES['foto_perfil']
        
        # Validar el tipo de archivo
        if foto.content_type not in ['image/png', 'image/jpeg', 'image/jpg']:
            messages.error(request, "Solo se permiten archivos PNG y JPG.")
            return redirect(redirect_url, **kwargs)
        
        # Validar el tamaño (1MB = 1048576 bytes)
        if foto.size > 1048576:
            messages.error(request, "El archivo es demasiado grande. El tamaño máximo permitido es 1MB.")
            return redirect(redirect_url, **kwargs)
        
        try:
            # Abrir la imagen con PIL
            img = Image.open(foto)
            
            # Mantener la relación de aspecto pero redimensionar si es muy grande
            max_size = (800, 800)
            img.thumbnail(max_size, Image.LANCZOS)
            
            # Determinar el formato de salida
            if foto.content_type == 'image/png':
                output_format = 'PNG'
            else:
                output_format = 'JPEG'
                
            # Crear un buffer para guardar la imagen comprimida
            output = BytesIO()
            
            # Guardar la imagen comprimida en el buffer
            if output_format == 'JPEG':
                img.save(output, format=output_format, quality=85, optimize=True)
            else:  # PNG
                img.save(output, format=output_format, optimize=True)
            
            # Crear un nuevo archivo desde el buffer
            output.seek(0)
            compressed_image = InMemoryUploadedFile(
                output,
                'ImageField',
                f"{foto.name.split('.')[0]}.{output_format.lower()}",
                f'image/{output_format.lower()}',
                sys.getsizeof(output),
                None
            )
            
            # Guardar la imagen comprimida en el usuario
            request.user.foto_perfil = compressed_image
            request.user.save()
            
            messages.success(request, "Foto de perfil actualizada correctamente.")
            
        except Exception as e:
            messages.error(request, f"Error al procesar la imagen: {str(e)}")
    else:
        messages.error(request, "No se ha seleccionado ninguna imagen.")
    
    return redirect(redirect_url, **kwargs)
