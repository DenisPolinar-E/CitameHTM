from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils import timezone
from django.utils.translation import gettext_lazy as _

# Choices para los modelos
SEXO_CHOICES = (
    ('M', 'Masculino'),
    ('F', 'Femenino'),
    ('O', 'Otro')
)

ESTADO_RESERVA_CHOICES = (
    ('activo', 'Activo'),
    ('bloqueado', 'Bloqueado'),
    ('supervisado', 'Supervisado')
)

ESTADO_CITA_CHOICES = (
    ('pendiente', 'Pendiente'),
    ('confirmada', 'Confirmada'),
    ('cancelada', 'Cancelada'),
    ('atendida', 'Atendida')
)

ESTADO_DERIVACION_CHOICES = (
    ('pendiente', 'Pendiente'),
    ('usada', 'Usada'),
    ('vencida', 'Vencida')
)

ESTADO_TRATAMIENTO_CHOICES = (
    ('activo', 'Activo'),
    ('terminado', 'Terminado'),
    ('cancelado', 'Cancelado')
)

TIPO_TURNO_CHOICES = (
    ('mañana', 'Mañana'),
    ('tarde', 'Tarde'),
    ('noche', 'Noche'),
    ('guardia', 'Guardia')
)

TIPO_NOTIFICACION_CHOICES = (
    ('confirmacion', 'Confirmación'),
    ('recordatorio', 'Recordatorio'),
    ('cancelacion', 'Cancelación'),
    ('advertencia', 'Advertencia'),
    ('informacion', 'Información')
)

DIAS_SEMANA_CHOICES = (
    (0, 'Lunes'),
    (1, 'Martes'),
    (2, 'Miércoles'),
    (3, 'Jueves'),
    (4, 'Viernes'),
    (5, 'Sábado'),
    (6, 'Domingo')
)

# Modelos
class Rol(models.Model):
    nombre = models.CharField(max_length=50)
    descripcion = models.TextField(blank=True)
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Rol'
        verbose_name_plural = 'Roles'

class Usuario(AbstractUser):
    nombres = models.CharField(max_length=100, blank=True)
    apellidos = models.CharField(max_length=100, blank=True)
    dni = models.CharField(max_length=8, unique=True, null=True, blank=True)
    telefono = models.CharField(max_length=15, blank=True)
    direccion = models.TextField(blank=True)
    fecha_nacimiento = models.DateField(null=True, blank=True)
    sexo = models.CharField(max_length=1, choices=SEXO_CHOICES, blank=True)
    rol = models.ForeignKey(Rol, on_delete=models.SET_NULL, null=True, related_name='usuarios')
    
    def __str__(self):
        return f"{self.nombres} {self.apellidos} ({self.dni})"
    
    class Meta:
        verbose_name = 'Usuario'
        verbose_name_plural = 'Usuarios'

class Paciente(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='paciente')
    representante = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, related_name='representados')
    faltas_consecutivas = models.PositiveIntegerField(default=0)
    estado_reserva = models.CharField(max_length=20, choices=ESTADO_RESERVA_CHOICES, default='activo')
    
    def __str__(self):
        return f"Paciente: {self.usuario.nombres} {self.usuario.apellidos}"
    
    class Meta:
        verbose_name = 'Paciente'
        verbose_name_plural = 'Pacientes'

class HistorialMedico(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='historiales')
    fecha = models.DateTimeField(auto_now_add=True)
    diagnostico = models.TextField()
    tratamiento = models.TextField()
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        return f"Historial de {self.paciente.usuario.nombres} - {self.fecha.strftime('%d/%m/%Y')}"
    
    class Meta:
        verbose_name = 'Historial Médico'
        verbose_name_plural = 'Historiales Médicos'
        ordering = ['-fecha']

class Especialidad(models.Model):
    nombre = models.CharField(max_length=100)
    descripcion = models.TextField(blank=True)
    acceso_directo = models.BooleanField(default=False, help_text='Si puede ser agendada sin derivación previa')
    
    def __str__(self):
        return self.nombre
    
    class Meta:
        verbose_name = 'Especialidad'
        verbose_name_plural = 'Especialidades'

class Medico(models.Model):
    usuario = models.OneToOneField(Usuario, on_delete=models.CASCADE, related_name='medico')
    cmp = models.CharField(max_length=10, verbose_name='Código Médico Profesional')
    especialidad = models.ForeignKey(Especialidad, on_delete=models.CASCADE, related_name='medicos')
    
    def __str__(self):
        return f"Dr. {self.usuario.nombres} {self.usuario.apellidos} - {self.especialidad.nombre}"
    
    class Meta:
        verbose_name = 'Médico'
        verbose_name_plural = 'Médicos'

class Consultorio(models.Model):
    codigo = models.CharField(max_length=10)
    piso = models.CharField(max_length=10)
    area = models.CharField(max_length=100)
    
    def __str__(self):
        return f"Consultorio {self.codigo} - Piso {self.piso} ({self.area})"
    
    class Meta:
        verbose_name = 'Consultorio'
        verbose_name_plural = 'Consultorios'

class DisponibilidadMedica(models.Model):
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='disponibilidades')
    dia_semana = models.IntegerField(choices=DIAS_SEMANA_CHOICES, null=True, blank=True)
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    tipo_turno = models.CharField(max_length=10, choices=TIPO_TURNO_CHOICES)
    fecha_especial = models.DateField(null=True, blank=True, help_text='Si es para un día específico')
    activo = models.BooleanField(default=True)
    
    def __str__(self):
        if self.fecha_especial:
            return f"{self.medico} - {self.fecha_especial.strftime('%d/%m/%Y')} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"
        else:
            return f"{self.medico} - {dict(DIAS_SEMANA_CHOICES)[self.dia_semana]} ({self.hora_inicio.strftime('%H:%M')} - {self.hora_fin.strftime('%H:%M')})"
    
    class Meta:
        verbose_name = 'Disponibilidad Médica'
        verbose_name_plural = 'Disponibilidades Médicas'

class Derivacion(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='derivaciones')
    medico_origen = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='derivaciones_realizadas')
    especialidad_destino = models.ForeignKey(Especialidad, on_delete=models.CASCADE, related_name='derivaciones_recibidas')
    fecha_derivacion = models.DateField(auto_now_add=True)
    motivo = models.TextField()
    vigencia_dias = models.PositiveIntegerField(default=30)
    estado = models.CharField(max_length=15, choices=ESTADO_DERIVACION_CHOICES, default='pendiente')
    cita_agendada = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Derivación de {self.paciente} a {self.especialidad_destino.nombre}"
        
    def esta_vigente(self):
        from datetime import timedelta
        fecha_vencimiento = self.fecha_derivacion + timedelta(days=self.vigencia_dias)
        return fecha_vencimiento >= timezone.now().date()
        
    class Meta:
        verbose_name = 'Derivación'
        verbose_name_plural = 'Derivaciones'

class TratamientoProgramado(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='tratamientos')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='tratamientos_programados')
    diagnostico = models.TextField()
    cantidad_sesiones = models.PositiveIntegerField()
    frecuencia_dias = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    estado = models.CharField(max_length=10, choices=ESTADO_TRATAMIENTO_CHOICES, default='activo')
    
    def __str__(self):
        return f"Tratamiento de {self.paciente} con {self.medico} - {self.cantidad_sesiones} sesiones"
    
    class Meta:
        verbose_name = 'Tratamiento Programado'
        verbose_name_plural = 'Tratamientos Programados'

class Cita(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='citas')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='citas')
    consultorio = models.ForeignKey(Consultorio, on_delete=models.CASCADE, related_name='citas')
    fecha = models.DateField()
    hora_inicio = models.TimeField()
    hora_fin = models.TimeField()
    estado = models.CharField(max_length=10, choices=ESTADO_CITA_CHOICES, default='pendiente')
    motivo = models.TextField()
    created_at = models.DateTimeField(auto_now_add=True)
    asistio = models.BooleanField(null=True, blank=True)
    fue_justificada = models.BooleanField(default=False)
    motivo_no_asistencia = models.TextField(blank=True)
    cita_anterior = models.ForeignKey('self', on_delete=models.SET_NULL, null=True, blank=True, related_name='citas_seguimiento')
    tratamiento = models.ForeignKey(TratamientoProgramado, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas')
    reservado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='citas_reservadas')
    derivacion = models.ForeignKey(Derivacion, on_delete=models.SET_NULL, null=True, blank=True, related_name='citas')
    
    def __str__(self):
        return f"Cita: {self.paciente} con {self.medico} - {self.fecha.strftime('%d/%m/%Y')} {self.hora_inicio.strftime('%H:%M')}"
    
    class Meta:
        verbose_name = 'Cita'
        verbose_name_plural = 'Citas'
        ordering = ['fecha', 'hora_inicio']

class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    tipo = models.CharField(max_length=15, choices=TIPO_NOTIFICACION_CHOICES)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    importante = models.BooleanField(default=False)
    
    def __str__(self):
        return f"Notificación para {self.usuario}: {self.mensaje[:30]}..."
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_envio']
