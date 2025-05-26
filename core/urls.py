from django.urls import path
from . import views
from . import views_paciente
from . import views_medico
from . import views_medico_atencion
from . import views_medico_historial
from . import api_views

urlpatterns = [
    # Vistas públicas
    path('', views.home, name='home'),
    path('login/', views.login_view, name='login'),
    path('registro/', views.registro_view, name='registro'),
    path('logout/', views.logout_view, name='logout'),
    
    # Dashboard principal y redirección según rol
    path('dashboard/', views.dashboard_view, name='dashboard'),
    
    # Dashboards específicos por rol
    path('dashboard/paciente/', views.dashboard_paciente, name='dashboard_paciente'),
    path('dashboard/medico/', views.dashboard_medico, name='dashboard_medico'),
    path('dashboard/admision/', views.dashboard_admision, name='dashboard_admision'),
    path('dashboard/admin/', views.dashboard_admin, name='dashboard_admin'),
    
    # API para dashboard dinámico
    path('api/dashboard/', views.api_dashboard, name='api_dashboard'),
    
    # APIs para notificaciones
    path('api/notificaciones/marcar-leida/', views.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('api/notificaciones/contador/', views.contador_notificaciones, name='contador_notificaciones'),
    
    # Aquí se agregarán más URLs para las funcionalidades específicas de cada rol
    
    # Funcionalidades para pacientes
    path('citas/reservar/', views_paciente.reservar_cita, name='reservar_cita'),
    
    # Funcionalidades para médicos
    path('disponibilidad/', views_medico.disponibilidad_medica, name='disponibilidad_medica'),
    path('disponibilidad/editar/<int:disponibilidad_id>/', views_medico.editar_disponibilidad, name='editar_disponibilidad'),
    path('disponibilidad/desactivar/<int:disponibilidad_id>/', views_medico.desactivar_disponibilidad, name='desactivar_disponibilidad'),
    path('disponibilidad/activar/<int:disponibilidad_id>/', views_medico.activar_disponibilidad, name='activar_disponibilidad'),
    path('historial-medico/', views_medico_historial.historial_medico, name='historial_medico'),
    
    # APIs para la reserva de citas
    path('api/medicos-por-especialidad/<int:especialidad_id>/', views_paciente.api_medicos_por_especialidad, name='api_medicos_por_especialidad'),
    path('api/horarios-disponibles/<int:medico_id>/<str:fecha>/', views_paciente.api_horarios_disponibles, name='api_horarios_disponibles'),
    
    # APIs para médicos
    path('api/disponibilidades-medico/', views_medico.api_disponibilidades_medico, name='api_disponibilidades_medico'),
    
    # Atención médica y derivaciones
    path('atencion/<int:cita_id>/', views_medico_atencion.atender_paciente, name='atender_paciente'),
    path('derivar/<int:cita_id>/', views_medico_atencion.derivar_paciente, name='derivar_paciente'),
    path('derivaciones/', views_medico_atencion.ver_derivaciones, name='ver_derivaciones'),
    
    # APIs para derivación médica
    path('api/derivacion/medicos-por-especialidad/<int:especialidad_id>/', api_views.medicos_por_especialidad, name='api_derivacion_medicos_por_especialidad'),
    path('api/derivacion/horarios-disponibles/<int:medico_id>/<str:fecha>/', api_views.horarios_disponibles, name='api_derivacion_horarios_disponibles'),
]
