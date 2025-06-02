from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from .models import (
    Rol, Usuario, Especialidad, Medico, Paciente, Consultorio,
    DisponibilidadMedica, Derivacion, TratamientoProgramado, Cita,
    DatosAntropometricos, Notificacion, HistorialMedico
)

# Configuración personalizada para el modelo Usuario
class UsuarioAdmin(UserAdmin):
    list_display = ('username', 'dni', 'email', 'nombres', 'apellidos', 'rol', 'is_staff')
    list_filter = ('rol', 'is_active', 'is_staff', 'sexo')
    search_fields = ('username', 'dni', 'email', 'nombres', 'apellidos')
    ordering = ('apellidos', 'nombres')
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Información Personal', {'fields': ('nombres', 'apellidos', 'dni', 'email', 'fecha_nacimiento', 'sexo', 'telefono', 'direccion')}),
        ('Permisos', {'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions')}),
        ('Rol en el Sistema', {'fields': ('rol',)}),
        ('Fechas Importantes', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'dni', 'password1', 'password2', 'nombres', 'apellidos', 'email', 'rol'),
        }),
    )

# Configuración para el modelo Paciente
class PacienteAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'get_dni', 'faltas_consecutivas', 'estado_reserva')
    list_filter = ('estado_reserva', 'faltas_consecutivas')
    search_fields = ('usuario__nombres', 'usuario__apellidos', 'usuario__dni')
    
    def get_nombre_completo(self, obj):
        return f"{obj.usuario.nombres} {obj.usuario.apellidos}"
    get_nombre_completo.short_description = 'Nombre Completo'
    
    def get_dni(self, obj):
        return obj.usuario.dni
    get_dni.short_description = 'DNI'

# Configuración para el modelo Médico
class MedicoAdmin(admin.ModelAdmin):
    list_display = ('get_nombre_completo', 'get_dni', 'cmp', 'especialidad')
    list_filter = ('especialidad',)
    search_fields = ('usuario__nombres', 'usuario__apellidos', 'usuario__dni', 'cmp')
    
    def get_nombre_completo(self, obj):
        return f"{obj.usuario.nombres} {obj.usuario.apellidos}"
    get_nombre_completo.short_description = 'Nombre Completo'
    
    def get_dni(self, obj):
        return obj.usuario.dni
    get_dni.short_description = 'DNI'

# Configuración para el modelo Cita
class CitaAdmin(admin.ModelAdmin):
    list_display = ('id', 'paciente', 'medico', 'fecha', 'hora_inicio', 'hora_fin', 'estado', 'asistio')
    list_filter = ('estado', 'fecha', 'asistio', 'fue_justificada')
    search_fields = ('paciente__usuario__nombres', 'paciente__usuario__apellidos', 'medico__usuario__nombres', 'medico__usuario__apellidos')
    date_hierarchy = 'fecha'

# Configuración para el modelo Especialidad
class EspecialidadAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'acceso_directo')
    list_filter = ('acceso_directo',)
    search_fields = ('nombre',)

# Configuración para el modelo Consultorio
class ConsultorioAdmin(admin.ModelAdmin):
    list_display = ('codigo', 'piso', 'area')
    list_filter = ('piso', 'area')
    search_fields = ('codigo', 'area')

# Configuración para el modelo DisponibilidadMedica
class DisponibilidadMedicaAdmin(admin.ModelAdmin):
    list_display = ('medico', 'dia_semana', 'fecha_especial', 'hora_inicio', 'hora_fin', 'tipo_turno', 'activo')
    list_filter = ('dia_semana', 'tipo_turno', 'activo')
    search_fields = ('medico__usuario__nombres', 'medico__usuario__apellidos')

# Configuración para el modelo Derivacion
class DerivacionAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico_origen', 'especialidad_destino', 'fecha_derivacion', 'estado', 'vigencia_dias')
    list_filter = ('estado', 'especialidad_destino')
    search_fields = ('paciente__usuario__nombres', 'paciente__usuario__apellidos', 'medico_origen__usuario__nombres')

# Configuración para el modelo TratamientoProgramado
class TratamientoProgramadoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'medico', 'cantidad_sesiones', 'fecha_inicio', 'estado')
    list_filter = ('estado',)
    search_fields = ('paciente__usuario__nombres', 'paciente__usuario__apellidos', 'diagnostico')

# Configuración para el modelo HistorialMedico
class HistorialMedicoAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha', 'diagnostico')
    list_filter = ('fecha',)
    search_fields = ('paciente__usuario__nombres', 'paciente__usuario__apellidos', 'diagnostico', 'tratamiento')
    date_hierarchy = 'fecha'

# Configuración para el modelo DatosAntropometricos
class DatosAntropometricosAdmin(admin.ModelAdmin):
    list_display = ('paciente', 'fecha_registro', 'peso', 'talla', 'imc', 'get_categoria_imc', 'registrado_por')
    list_filter = ('fecha_registro',)
    search_fields = ('paciente__usuario__nombres', 'paciente__usuario__apellidos', 'registrado_por__nombres')
    date_hierarchy = 'fecha_registro'
    
    def get_categoria_imc(self, obj):
        return obj.get_categoria_imc()
    get_categoria_imc.short_description = 'Categoría IMC'

# Configuración para el modelo Notificacion
class NotificacionAdmin(admin.ModelAdmin):
    list_display = ('usuario', 'tipo', 'fecha_envio', 'leido', 'importante')
    list_filter = ('tipo', 'leido', 'importante', 'fecha_envio')
    search_fields = ('usuario__nombres', 'usuario__apellidos', 'mensaje')
    date_hierarchy = 'fecha_envio'

# Configuración para el modelo Rol
class RolAdmin(admin.ModelAdmin):
    list_display = ('nombre', 'descripcion')
    search_fields = ('nombre',)

# Registrar modelos en el admin
admin.site.register(Usuario, UsuarioAdmin)
admin.site.register(Rol, RolAdmin)
admin.site.register(Paciente, PacienteAdmin)
admin.site.register(Medico, MedicoAdmin)
admin.site.register(Especialidad, EspecialidadAdmin)
admin.site.register(Consultorio, ConsultorioAdmin)
admin.site.register(DisponibilidadMedica, DisponibilidadMedicaAdmin)
admin.site.register(Cita, CitaAdmin)
admin.site.register(Derivacion, DerivacionAdmin)
admin.site.register(TratamientoProgramado, TratamientoProgramadoAdmin)
admin.site.register(HistorialMedico, HistorialMedicoAdmin)
admin.site.register(DatosAntropometricos, DatosAntropometricosAdmin)
admin.site.register(Notificacion, NotificacionAdmin)
