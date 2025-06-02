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
    foto_perfil = models.ImageField(upload_to='fotos_perfil/', null=True, blank=True)
    
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
    sesiones_completadas = models.PositiveIntegerField(default=0)
    frecuencia_dias = models.PositiveIntegerField()
    fecha_inicio = models.DateField()
    fecha_fin_estimada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=10, choices=ESTADO_TRATAMIENTO_CHOICES, default='activo')
    notas_seguimiento = models.TextField(blank=True, help_text='Notas generales sobre el progreso del tratamiento')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Tratamiento de {self.paciente} con {self.medico} - {self.cantidad_sesiones} sesiones"
    
    def progreso(self):
        """Retorna el porcentaje de progreso del tratamiento"""
        if self.cantidad_sesiones > 0:
            return int((self.sesiones_completadas / self.cantidad_sesiones) * 100)
        return 0
    
    def calcular_fecha_fin(self):
        """Calcula la fecha estimada de finalización basada en la frecuencia y cantidad de sesiones"""
        from datetime import timedelta
        if self.fecha_inicio and self.frecuencia_dias and self.cantidad_sesiones:
            dias_totales = self.frecuencia_dias * (self.cantidad_sesiones - 1)
            return self.fecha_inicio + timedelta(days=dias_totales)
        return None
    
    def save(self, *args, **kwargs):
        # Calcular fecha fin estimada si no está establecida
        if not self.fecha_fin_estimada:
            self.fecha_fin_estimada = self.calcular_fecha_fin()
        super().save(*args, **kwargs)
    
    class Meta:
        verbose_name = 'Tratamiento Programado'
        verbose_name_plural = 'Tratamientos Programados'
        ordering = ['-created_at']


class SeguimientoSesion(models.Model):
    """Modelo para registrar cada sesión de seguimiento de un tratamiento"""
    tratamiento = models.ForeignKey(TratamientoProgramado, on_delete=models.CASCADE, related_name='sesiones')
    cita = models.OneToOneField('Cita', on_delete=models.SET_NULL, null=True, blank=True, related_name='seguimiento_sesion')
    numero_sesion = models.PositiveIntegerField()
    fecha_programada = models.DateField()
    fecha_realizada = models.DateField(null=True, blank=True)
    estado = models.CharField(max_length=15, choices=(
        ('pendiente', 'Pendiente'),
        ('completada', 'Completada'),
        ('cancelada', 'Cancelada'),
        ('reprogramada', 'Reprogramada')
    ), default='pendiente')
    observaciones = models.TextField(blank=True)
    evolucion = models.TextField(blank=True, help_text='Evolución del paciente en esta sesión')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"Sesión {self.numero_sesion} de {self.tratamiento}"
    
    def marcar_completada(self, observaciones=None, evolucion=None):
        """Marca la sesión como completada y actualiza el tratamiento"""
        self.estado = 'completada'
        self.fecha_realizada = timezone.now().date()
        
        if observaciones:
            self.observaciones = observaciones
        if evolucion:
            self.evolucion = evolucion
            
        self.save()
        
        # Actualizar el contador de sesiones completadas en el tratamiento
        tratamiento = self.tratamiento
        tratamiento.sesiones_completadas += 1
        
        # Si se completaron todas las sesiones, marcar el tratamiento como terminado
        if tratamiento.sesiones_completadas >= tratamiento.cantidad_sesiones:
            tratamiento.estado = 'terminado'
            
        tratamiento.save()
    
    class Meta:
        verbose_name = 'Seguimiento de Sesión'
        verbose_name_plural = 'Seguimientos de Sesiones'
        ordering = ['tratamiento', 'numero_sesion']
        unique_together = ['tratamiento', 'numero_sesion']

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


class DatosAntropometricos(models.Model):
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='datos_antropometricos')
    fecha_registro = models.DateField(auto_now_add=True)
    peso = models.DecimalField(max_digits=5, decimal_places=2, help_text="Peso en kilogramos")
    talla = models.DecimalField(max_digits=5, decimal_places=2, help_text="Altura en centímetros")
    imc = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True, help_text="Índice de Masa Corporal")
    medico = models.ForeignKey('Medico', on_delete=models.SET_NULL, null=True, blank=True, related_name='datos_registrados')
    registrado_por = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, related_name='registros_antropometricos')
    cita = models.ForeignKey(Cita, on_delete=models.SET_NULL, null=True, blank=True, related_name='datos_antropometricos')
    
    def save(self, *args, **kwargs):
        # Calcular IMC automáticamente si no está establecido
        if self.peso and self.talla and (not self.imc or self.imc == 0):
            # Convertir talla de cm a metros
            talla_metros = self.talla / 100
            self.imc = round(self.peso / (talla_metros * talla_metros), 2)
        super().save(*args, **kwargs)
    
    def get_categoria_imc(self):
        """Retorna la categoría del IMC según los estándares de la OMS"""
        if not self.imc:
            return "No calculado"
        
        if self.imc < 18.5:
            return "Bajo peso"
        elif self.imc < 25:
            return "Normal"
        elif self.imc < 30:
            return "Sobrepeso"
        else:
            return "Obesidad"
    
    def __str__(self):
        return f"Datos de {self.paciente.usuario.get_full_name()} - {self.fecha_registro}"
    
    class Meta:
        verbose_name = 'Datos Antropométricos'
        verbose_name_plural = 'Datos Antropométricos'
        ordering = ['-fecha_registro']
        
    def __str__(self):
        return f"Datos de {self.paciente} - {self.fecha_registro.strftime('%d/%m/%Y')}"

class Notificacion(models.Model):
    usuario = models.ForeignKey(Usuario, on_delete=models.CASCADE, related_name='notificaciones')
    mensaje = models.TextField()
    tipo = models.CharField(max_length=15, choices=TIPO_NOTIFICACION_CHOICES)
    fecha_envio = models.DateTimeField(auto_now_add=True)
    leido = models.BooleanField(default=False)
    importante = models.BooleanField(default=False)
    url_redireccion = models.CharField(max_length=255, blank=True, null=True, help_text="URL a la que redirigir al hacer clic en la notificación")
    objeto_relacionado = models.CharField(max_length=50, blank=True, null=True, help_text="Tipo de objeto relacionado (ej: 'cita', 'derivacion')")
    objeto_id = models.PositiveIntegerField(blank=True, null=True, help_text="ID del objeto relacionado")
    fecha_lectura = models.DateTimeField(null=True, blank=True)
    
    def __str__(self):
        return f"Notificación para {self.usuario}: {self.mensaje[:30]}..."
    
    def get_icono(self):
        """Retorna el icono de Font Awesome según el tipo de notificación"""
        iconos = {
            'confirmacion': 'check-circle',
            'recordatorio': 'clock',
            'cancelacion': 'times-circle',
            'advertencia': 'exclamation-triangle',
            'informacion': 'info-circle'
        }
        return iconos.get(self.tipo, 'bell')
    
    def marcar_como_leida(self):
        """Marca la notificación como leída y guarda la fecha de lectura"""
        self.leido = True
        self.fecha_lectura = timezone.now()
        self.save()
    
    class Meta:
        verbose_name = 'Notificación'
        verbose_name_plural = 'Notificaciones'
        ordering = ['-fecha_envio']
