from django.shortcuts import render, redirect
from django.contrib.auth.decorators import login_required
from django.contrib import messages
from django.utils import timezone
from django.db.models import Q
from datetime import datetime, timedelta
import calendar

from .models import Medico, Cita, Paciente, Usuario
from .decorators import medico_required

class AgendaBase:
    """
    Clase base para implementar agendas para diferentes roles.
    Implementa el patrón de variabilidad para permitir diferentes
    comportamientos según el rol del usuario.
    """
    def __init__(self, usuario, fecha=None):
        self.usuario = usuario
        self.fecha = fecha or timezone.now().date()
        self.fecha_inicio_semana = self.fecha - timedelta(days=self.fecha.weekday())
        self.fecha_fin_semana = self.fecha_inicio_semana + timedelta(days=6)
    
    def get_eventos_dia(self):
        """Método base para obtener eventos del día actual"""
        raise NotImplementedError("Las subclases deben implementar este método")
    
    def get_eventos_semana(self):
        """Método base para obtener eventos de la semana actual"""
        raise NotImplementedError("Las subclases deben implementar este método")
    
    def get_estadisticas(self):
        """Método base para obtener estadísticas"""
        raise NotImplementedError("Las subclases deben implementar este método")
    
    def get_context_data(self):
        """Método base para obtener el contexto para la plantilla"""
        return {
            'fecha_actual': self.fecha,
            'fecha_inicio_semana': self.fecha_inicio_semana,
            'fecha_fin_semana': self.fecha_fin_semana,
            'dias_semana': self._get_dias_semana(),
            'eventos_dia': self.get_eventos_dia(),
            'eventos_semana': self.get_eventos_semana(),
            'estadisticas': self.get_estadisticas(),
        }
    
    def _get_dias_semana(self):
        """Retorna los días de la semana actual para mostrar en el calendario"""
        dias = []
        for i in range(7):
            fecha = self.fecha_inicio_semana + timedelta(days=i)
            dias.append({
                'fecha': fecha,
                'nombre': calendar.day_name[fecha.weekday()],
                'es_hoy': fecha == timezone.now().date()
            })
        return dias


class MedicoAgenda(AgendaBase):
    """Implementación específica de agenda para médicos"""
    
    def __init__(self, usuario, fecha=None):
        super().__init__(usuario, fecha)
        self.medico = Medico.objects.get(usuario=usuario)
    
    def get_eventos_dia(self):
        """Obtiene las citas del médico para el día actual"""
        return Cita.objects.filter(
            medico=self.medico,
            fecha=self.fecha
        ).order_by('hora_inicio')
    
    def get_eventos_semana(self):
        """Obtiene las citas del médico para la semana actual"""
        eventos_semana = {}
        for i in range(7):
            fecha = self.fecha_inicio_semana + timedelta(days=i)
            eventos_semana[fecha] = Cita.objects.filter(
                medico=self.medico,
                fecha=fecha
            ).order_by('hora_inicio')
        return eventos_semana
    
    def get_estadisticas(self):
        """Obtiene estadísticas relevantes para el médico"""
        # Citas del día
        citas_hoy = Cita.objects.filter(
            medico=self.medico,
            fecha=timezone.now().date()
        )
        
        # Citas pendientes (no atendidas)
        citas_pendientes = citas_hoy.filter(
            estado__in=['pendiente', 'confirmada']
        ).count()
        
        # Citas atendidas hoy
        citas_atendidas_hoy = citas_hoy.filter(
            estado='atendida'
        ).count()
        
        # Total de citas del día
        total_citas_hoy = citas_hoy.count()
        
        # Porcentaje de avance del día
        porcentaje_avance = 0
        if total_citas_hoy > 0:
            porcentaje_avance = (citas_atendidas_hoy / total_citas_hoy) * 100
        
        return {
            'citas_pendientes': citas_pendientes,
            'citas_atendidas_hoy': citas_atendidas_hoy,
            'total_citas_hoy': total_citas_hoy,
            'porcentaje_avance': porcentaje_avance,
            'proxima_cita': self._get_proxima_cita()
        }
    
    def _get_proxima_cita(self):
        """Obtiene la próxima cita pendiente del médico"""
        ahora = timezone.now()
        return Cita.objects.filter(
            medico=self.medico,
            fecha=ahora.date(),
            hora_inicio__gte=ahora.time(),
            estado__in=['pendiente', 'confirmada']
        ).order_by('hora_inicio').first()


@login_required
@medico_required
def mi_agenda(request):
    """Vista para mostrar la agenda del médico"""
    try:
        # Verificar que el usuario tenga un médico asociado
        try:
            medico = Medico.objects.get(usuario=request.user)
        except Medico.DoesNotExist:
            messages.error(request, 'No tienes un perfil de médico asociado a tu cuenta.')
            return redirect('dashboard_medico')
        
        # Obtener fecha seleccionada (si se proporciona)
        fecha_str = request.GET.get('fecha')
        fecha = None
        if fecha_str:
            try:
                fecha = datetime.strptime(fecha_str, '%Y-%m-%d').date()
            except ValueError:
                fecha = None
        
        # Crear instancia de la agenda
        agenda = MedicoAgenda(request.user, fecha)
        
        # Obtener contexto
        context = agenda.get_context_data()
        
        # Agregar información adicional al contexto
        context['medico'] = medico
        context['titulo_pagina'] = 'Mi Agenda'
        
        return render(request, 'medico/mi_agenda.html', context)
    
    except Exception as e:
        messages.error(request, f'Error al cargar la agenda: {str(e)}')
        return redirect('dashboard_medico')
