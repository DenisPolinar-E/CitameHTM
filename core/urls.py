from django.urls import path
from . import views
from . import views_paciente
from . import views_medico
from . import views_medico_atencion
from . import views_medico_historial
from . import views_paciente_citas
from . import views_paciente_historial
from . import views_perfil
from . import views_admin_historial
from . import views_admision
from . import views_reportes
from . import views_agenda
from . import views_seguimiento
from . import views_farmacia
from . import views_tendencias
from . import api_views
from . import api_views_pacientes
from . import api_views_notificaciones
from . import api_views_analisis_origen



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
    path('mis-citas/', views_paciente_citas.mis_citas, name='mis_citas'),
    path('citas/cancelar/<int:cita_id>/', views_paciente_citas.cancelar_cita, name='cancelar_cita'),
    path('mi-historial-medico/', views_paciente_historial.mi_historial_medico, name='mi_historial_medico'),
    # URLs para perfiles de usuario (unificado)
    # Rutas para perfiles de pacientes
    path('perfil/paciente/', views_perfil.perfil_usuario, {'tipo': 'paciente'}, name='perfil_paciente'),
    path('perfil/paciente/<int:usuario_id>/', views_perfil.perfil_usuario, {'tipo': 'paciente'}, name='perfil_paciente_id'),
    # Rutas para perfiles de médicos
    path('perfil/medico/', views_perfil.perfil_usuario, {'tipo': 'medico'}, name='perfil_medico'),
    path('perfil/medico/<int:usuario_id>/', views_perfil.perfil_usuario, {'tipo': 'medico'}, name='perfil_medico_id'),
    # Rutas para perfiles de admisión
    path('perfil/admision/', views_perfil.perfil_usuario, {'tipo': 'admision'}, name='perfil_admision'),
    path('perfil/admision/<int:usuario_id>/', views_perfil.perfil_usuario, {'tipo': 'admision'}, name='perfil_admision_id'),
    # Rutas para perfiles de administrador
    path('perfil/admin/', views_perfil.perfil_usuario, {'tipo': 'admin'}, name='perfil_admin'),
    path('perfil/admin/<int:usuario_id>/', views_perfil.perfil_usuario, {'tipo': 'admin'}, name='perfil_admin_id'),
    # Ruta para subir foto de perfil
    path('perfil/subir-foto/', views_perfil.subir_foto_perfil, name='subir_foto_perfil'),
    # Redirigir la URL genérica al dashboard
    path('perfil/', views.dashboard_view, name='perfil_usuario'),
    
    # Funcionalidades para médicos
    path('disponibilidad/', views_medico.disponibilidad_medica, name='disponibilidad_medica'),
    path('disponibilidad/editar/<int:disponibilidad_id>/', views_medico.editar_disponibilidad, name='editar_disponibilidad'),
    path('disponibilidad/desactivar/<int:disponibilidad_id>/', views_medico.desactivar_disponibilidad, name='desactivar_disponibilidad'),
    path('disponibilidad/activar/<int:disponibilidad_id>/', views_medico.activar_disponibilidad, name='activar_disponibilidad'),
    path('gestion-citas/', views_medico.gestion_citas, name='gestion_citas'),
    path('historial-medico/', views_medico_historial.historial_medico, name='historial_medico'),
    path('registrar-datos-antropometricos/<int:paciente_id>/', views_medico_historial.registrar_datos_antropometricos, name='registrar_datos_antropometricos'),
    path('api/horarios-disponibles/<int:medico_id>/<str:fecha>/', views_paciente.api_horarios_disponibles, name='api_horarios_disponibles'),
    
    # Funcionalidades para médicos
    # Comentamos temporalmente las URLs que hacen referencia a funciones que no existen
    # path('disponibilidad/', views_medico.disponibilidad_medica, name='disponibilidad_medica'),
    # path('atender-pacientes/', views_medico.atender_pacientes, name='atender_pacientes'),
    path('historial-medico/', views_medico_historial.historial_medico, name='historial_medico'),
    # path('derivar-especialista/', views_medico.derivar_especialista, name='derivar_especialista'),
    # path('programar-seguimientos/', views_medico.programar_seguimientos, name='programar_seguimientos'),
    # Rutas para Mi Agenda (dos rutas alternativas que apuntan a la misma funcionalidad)
    path('mi-agenda/', views_agenda.mi_agenda, name='mi_agenda'),
    path('agenda/', views_medico.mi_agenda_medico, name='agenda_medico'),
    
    # APIs para médicos
    # path('api/disponibilidades-medico/', views_medico.api_disponibilidades_medico, name='api_disponibilidades_medico'),
    
    # Atención médica y derivaciones
    path('atencion/<int:cita_id>/', views_medico_atencion.atender_paciente, name='atender_paciente'),
    path('derivar/<int:cita_id>/', views_medico_atencion.derivar_paciente, name='derivar_paciente'),
    path('derivaciones/', views_medico_atencion.ver_derivaciones, name='ver_derivaciones'),
    
    # Funcionalidades para administradores
    path('administrador/historial-medico/', views_admin_historial.admin_historial_medico, name='admin_historial_medico'),
    
    # Funcionalidades para personal de admisión
    path('citas/crear/', views_admision.registrar_cita, name='registrar_cita'),
    
    # APIs para derivación médica
    path('api/derivacion/medicos-por-especialidad/<int:especialidad_id>/', api_views.medicos_por_especialidad, name='api_derivacion_medicos_por_especialidad'),
    
    # API para pacientes - médicos por especialidad
    path('api/medicos-por-especialidad/<int:especialidad_id>/', views_paciente.api_medicos_por_especialidad, name='api_pacientes_medicos_por_especialidad'),
    
    # APIs para notificaciones
    path('api/marcar-notificaciones-leidas/', api_views_notificaciones.marcar_notificaciones_leidas, name='marcar_notificaciones_leidas'),
    path('api/marcar-notificacion-leida/<int:notificacion_id>/', api_views_notificaciones.marcar_notificacion_leida, name='marcar_notificacion_leida'),
    path('api/eliminar-notificacion/<int:notificacion_id>/', api_views_notificaciones.eliminar_notificacion, name='eliminar_notificacion'),
    path('api/notificaciones-no-leidas-count/', api_views_notificaciones.notificaciones_no_leidas_count, name='notificaciones_no_leidas_count'),
    path('api/limpiar-notificaciones-citas-atendidas/', api_views_notificaciones.limpiar_notificaciones_citas_atendidas, name='limpiar_notificaciones_citas_atendidas'),
    path('api/derivacion/horarios-disponibles/<int:medico_id>/<str:fecha>/', api_views.horarios_disponibles, name='api_derivacion_horarios_disponibles'),
    
    # APIs para búsqueda de pacientes
    path('api/pacientes/buscar/', views_admision.buscar_pacientes_api, name='api_buscar_pacientes'),
    
    # Rutas para seguimiento de pacientes
    path('seguimientos/', views_seguimiento.ver_seguimientos, name='ver_seguimientos'),
    path('seguimientos/programar/', views_seguimiento.programar_seguimientos, name='programar_seguimientos'),
    path('seguimientos/detalle/<int:tratamiento_id>/', views_seguimiento.detalle_seguimiento, name='detalle_seguimiento'),
    path('seguimientos/programar-cita/<int:sesion_id>/', views_seguimiento.programar_cita_sesion, name='programar_cita_sesion'),
    path('seguimientos/atender-sesion/<int:sesion_id>/', views_seguimiento.atender_sesion_seguimiento, name='atender_sesion_seguimiento'),
    path('seguimientos/registrar-evolucion/<int:sesion_id>/', views_seguimiento.registrar_evolucion, name='registrar_evolucion'),
    path('seguimientos/cancelar/<int:tratamiento_id>/', views_seguimiento.cancelar_tratamiento, name='cancelar_tratamiento'),
    path('mis-tratamientos/', views_seguimiento.mis_tratamientos, name='mis_tratamientos'),
    
    # APIs para seguimiento
    path('api/sesiones-pendientes/', views_seguimiento.api_sesiones_pendientes, name='api_sesiones_pendientes'),
    path('api/buscar-medicamentos-prescripcion/', views_seguimiento.api_buscar_medicamentos_prescripcion, name='api_buscar_medicamentos_prescripcion'),
    
    # === FARMACIA ===
    path('farmacia/', views_farmacia.dashboard_farmacia, name='dashboard_farmacia'),
    path('farmacia/recetas/', views_farmacia.recetas_pendientes, name='recetas_pendientes'),
    path('farmacia/receta/<int:receta_id>/', views_farmacia.detalle_receta, name='detalle_receta'),
    path('farmacia/dispensar/<int:receta_id>/', views_farmacia.dispensar_receta, name='dispensar_receta'),
    path('farmacia/inventario/', views_farmacia.inventario_medicamentos, name='inventario_medicamentos'),
    path('farmacia/inventario/entrada/', views_farmacia.entrada_medicamentos, name='entrada_medicamentos'),
    path('farmacia/inventario/ajuste/', views_farmacia.ajuste_inventario, name='ajuste_inventario'),
    path('farmacia/inventario/historial/', views_farmacia.historial_movimientos, name='historial_movimientos'),
    path('farmacia/inventario/medicamento/<int:medicamento_id>/', views_farmacia.detalle_medicamento_inventario, name='detalle_medicamento_inventario'),
    path('farmacia/inventario/reporte/', views_farmacia.reporte_inventario, name='reporte_inventario'),
    path('farmacia/alertas/', views_farmacia.alertas_farmacia, name='alertas_farmacia'),
    
    # APIs para farmacia
    path('api/farmacia/buscar-medicamento/', views_farmacia.api_buscar_medicamento, name='api_buscar_medicamento'),
    path('api/farmacia/estadisticas/', views_farmacia.api_estadisticas_farmacia, name='api_estadisticas_farmacia'),
    
    # Reportes y análisis estadísticos
    # Análisis Temporal
    path('administrador/analisis-temporal/distribucion/', views_reportes.distribucion_citas, name='distribucion_citas'),
    path('administrador/analisis-temporal/comparativas/', views.comparativas_citas, name='comparativas'),
    path('administrador/analisis-temporal/tendencias/', views_tendencias.tendencias_citas, name='tendencias'),
    path('administrador/analisis-temporal/asistencia/', views.tasas_asistencia, name='tasas_asistencia'),
    
    # Análisis por Origen
    path('administrador/analisis-origen/admision/', views_reportes.citas_admision, name='citas_admision'),
    path('administrador/analisis-origen/derivacion/', views_reportes.origen_citas, name='citas_derivacion'),
    path('administrador/analisis-origen/seguimiento/', views_reportes.citas_seguimiento, name='citas_seguimiento'),
    path('administrador/analisis-origen/', views_reportes.origen_citas, name='origen_citas'),
    
    # Análisis por Especialidad y Médico
    path('administrador/analisis-especialidad/', views_reportes.analisis_especialidad, name='analisis_especialidad'),
    path('administrador/analisis-medico/', views_reportes.analisis_medico, name='analisis_medico'),
    
    # Análisis de Estado
    path('administrador/analisis-estado/completadas/', views_reportes.citas_completadas, name='citas_completadas'),
    path('administrador/analisis-estado/canceladas/', views_reportes.citas_canceladas, name='citas_canceladas'),
    path('administrador/analisis-estado/inasistencias/', views_reportes.citas_inasistencias, name='citas_inasistencias'),
    
    # Reportes Especiales
    path('administrador/especiales/pacientes/', views_reportes.reporte_pacientes, name='reporte_pacientes'),
    path('administrador/especiales/satisfaccion/', views_reportes.reporte_satisfaccion, name='reporte_satisfaccion'),
    path('administrador/especiales/indicadores/', views_reportes.indicadores_clave, name='indicadores_clave'),
    
    # APIs para reportes
    path('api/medicos-por-especialidad/', views_reportes.api_medicos_por_especialidad, name='api_medicos_por_especialidad'),
    path('api/distribucion-citas/', views_reportes.api_distribucion_citas, name='api_distribucion_citas'),
    path('api/comparativa-citas/', views.api_comparativa_citas, name='api_comparativa_citas'),
    path('api/tendencias-citas/', views_tendencias.api_tendencias_citas, name='api_tendencias_citas'),
    path('api/medicos-por-especialidad-tendencias/', views_tendencias.api_medicos_por_especialidad_tendencias, name='api_medicos_por_especialidad_tendencias'),
    path('api/tasas-asistencia/', views.api_tasas_asistencia, name='api_tasas_asistencia'),
    
    # APIs para análisis por origen
    path('api/citas/origen/', api_views_analisis_origen.api_origen_citas, name='api_origen_citas'),
    # Las siguientes líneas fueron comentadas porque los métodos no existen
    # path('api/derivaciones/estadisticas/', api_views.api_derivaciones, name='api_derivaciones'),
    # path('api/citas/distribucion/', api_views.api_distribucion_citas, name='api_distribucion_citas'),
    # path('api/asistencia/tasas/', api_views.api_tasas_asistencia, name='api_tasas_asistencia'),
    path('administrador/reportes-farmacia/consumo-medicamentos/', views.admin_reporte_consumo_medicamentos, name='admin_reporte_consumo_medicamentos')
]
