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

# Choices para farmacia
ESTADO_RECETA_CHOICES = (
    ('pendiente', 'Pendiente'),
    ('dispensada', 'Dispensada'),
    ('parcial', 'Parcialmente Dispensada'),
    ('cancelada', 'Cancelada'),
)

FORMA_FARMACEUTICA_CHOICES = (
    ('tableta', 'Tableta'),
    ('capsula', 'Cápsula'),
    ('jarabe', 'Jarabe'),
    ('suspension', 'Suspensión'),
    ('crema', 'Crema'),
    ('pomada', 'Pomada'),
    ('solucion', 'Solución'),
    ('inyectable', 'Inyectable'),
    ('gotas', 'Gotas'),
    ('spray', 'Spray'),
    ('ovulo', 'Óvulo'),
    ('supositorio', 'Supositorio'),
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
    
    # === CAMPOS FARMACOLÓGICOS INTEGRADOS ===
    sintomas_actuales = models.TextField(blank=True, help_text="Síntomas presentes en esta sesión")
    mejoria_observada = models.TextField(blank=True, help_text="Mejorías observadas desde la última sesión")
    requiere_ajuste_medicamentos = models.BooleanField(default=False, 
                                                        help_text="Indica si requiere ajuste farmacológico")
    observaciones_farmacologicas = models.TextField(blank=True, 
                                                     help_text="Observaciones sobre medicamentos y dosis")
    receta_seguimiento = models.ForeignKey('RecetaMedica', on_delete=models.SET_NULL, null=True, blank=True,
                                           help_text="Receta generada en esta sesión")
    proxima_sesion_recomendada = models.BooleanField(default=True)
    observaciones_proxima_sesion = models.TextField(blank=True)
    
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


# === MODELOS DE FARMACIA ===

class Medicamento(models.Model):
    codigo = models.CharField(max_length=20, unique=True, help_text="Código interno del medicamento")
    nombre_generico = models.CharField(max_length=200, help_text="Nombre del principio activo")
    nombre_comercial = models.CharField(max_length=200, help_text="Marca comercial")
    concentracion = models.CharField(max_length=100, help_text="Ej: 500mg, 250mg/5ml")
    forma_farmaceutica = models.CharField(max_length=20, choices=FORMA_FARMACEUTICA_CHOICES, default='tableta')
    laboratorio = models.CharField(max_length=100)
    
    # Control de inventario
    stock_actual = models.IntegerField(default=0, help_text="Cantidad actual en inventario")
    stock_minimo = models.IntegerField(default=10, help_text="Stock mínimo para alertas")
    precio_unitario = models.DecimalField(max_digits=10, decimal_places=2, help_text="Precio por unidad")
    
    # Fechas importantes
    fecha_vencimiento = models.DateField(help_text="Fecha de vencimiento del lote actual")
    fecha_ingreso = models.DateField(auto_now_add=True)
    
    # Control
    activo = models.BooleanField(default=True)
    requiere_receta = models.BooleanField(default=True, help_text="Si requiere prescripción médica")
    controlado = models.BooleanField(default=False, help_text="Si es medicamento controlado")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def __str__(self):
        return f"{self.nombre_comercial} ({self.nombre_generico}) - {self.concentracion}"
    
    def stock_disponible(self):
        """Verifica si hay stock disponible"""
        return self.stock_actual > 0
    
    def stock_critico(self):
        """Verifica si el stock está por debajo del mínimo"""
        return self.stock_actual <= self.stock_minimo
    
    def dias_para_vencer(self):
        """Calcula días hasta el vencimiento"""
        from datetime import date
        if self.fecha_vencimiento:
            delta = self.fecha_vencimiento - date.today()
            return delta.days
        return None
    
    def proximo_a_vencer(self, dias=30):
        """Verifica si está próximo a vencer en X días"""
        dias_restantes = self.dias_para_vencer()
        return dias_restantes is not None and dias_restantes <= dias
    
    class Meta:
        verbose_name = 'Medicamento'
        verbose_name_plural = 'Medicamentos'
        ordering = ['nombre_comercial']


class RecetaMedica(models.Model):
    # Vinculación con sistemas existentes
    cita = models.ForeignKey(Cita, on_delete=models.CASCADE, null=True, blank=True, related_name='recetas')
    sesion_seguimiento = models.ForeignKey(SeguimientoSesion, on_delete=models.CASCADE, null=True, blank=True, related_name='recetas')
    paciente = models.ForeignKey(Paciente, on_delete=models.CASCADE, related_name='recetas')
    medico = models.ForeignKey(Medico, on_delete=models.CASCADE, related_name='recetas_prescritas')
    
    # Información de la receta
    codigo_receta = models.CharField(max_length=20, unique=True, help_text="Código único de la receta")
    fecha_prescripcion = models.DateTimeField(auto_now_add=True)
    fecha_dispensacion = models.DateTimeField(null=True, blank=True)
    estado = models.CharField(max_length=20, choices=ESTADO_RECETA_CHOICES, default='pendiente')
    observaciones_medico = models.TextField(blank=True, help_text="Observaciones del médico prescriptor")
    observaciones_farmacia = models.TextField(blank=True, help_text="Observaciones del farmacéutico")
    
    # Farmacéutico que dispensa
    farmaceutico = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True, 
                                     related_name='recetas_dispensadas',
                                     help_text="Farmacéutico que dispensó la receta")
    
    # Control
    vigencia_dias = models.IntegerField(default=30, help_text="Días de vigencia de la receta")
    urgente = models.BooleanField(default=False, help_text="Si es una receta urgente")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    def save(self, *args, **kwargs):
        if not self.codigo_receta:
            # Generar código único
            import uuid
            self.codigo_receta = f"RX-{str(uuid.uuid4())[:8].upper()}"
        super().save(*args, **kwargs)
    
    def __str__(self):
        return f"Receta {self.codigo_receta} - {self.paciente} ({self.fecha_prescripcion.strftime('%d/%m/%Y')})"
    
    def esta_vigente(self):
        """Verifica si la receta está vigente"""
        from datetime import timedelta
        if self.fecha_prescripcion and self.vigencia_dias:
            fecha_vencimiento = self.fecha_prescripcion.date() + timedelta(days=self.vigencia_dias)
            return fecha_vencimiento >= timezone.now().date()
        return False
    
    def puede_dispensarse(self):
        """Verifica si la receta puede ser dispensada"""
        return self.estado == 'pendiente' and self.esta_vigente()
    
    def total_medicamentos(self):
        """Retorna el total de medicamentos en la receta"""
        return self.detalles.count()
    
    def total_dispensado(self):
        """Verifica si todos los medicamentos fueron dispensados"""
        total = self.detalles.count()
        dispensados = self.detalles.filter(cantidad_dispensada__gte=models.F('cantidad_prescrita')).count()
        return total == dispensados
    
    def marcar_dispensada(self, farmaceutico):
        """Marca la receta como dispensada"""
        self.estado = 'dispensada'
        self.fecha_dispensacion = timezone.now()
        self.farmaceutico = farmaceutico
        self.save()
    
    class Meta:
        verbose_name = 'Receta Médica'
        verbose_name_plural = 'Recetas Médicas'
        ordering = ['-fecha_prescripcion']


class DetalleReceta(models.Model):
    receta = models.ForeignKey(RecetaMedica, on_delete=models.CASCADE, related_name='detalles')
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE)
    
    # Prescripción médica
    cantidad_prescrita = models.IntegerField(help_text="Cantidad total prescrita")
    dosis = models.CharField(max_length=100, help_text="Ej: 1 tableta cada 8 horas")
    frecuencia = models.CharField(max_length=100, help_text="Ej: Cada 8 horas, 3 veces al día")
    duracion_dias = models.IntegerField(help_text="Duración del tratamiento en días")
    via_administracion = models.CharField(max_length=50, default='oral', help_text="Vía de administración")
    instrucciones = models.TextField(help_text="Instrucciones específicas de administración")
    
    # Dispensación
    cantidad_dispensada = models.IntegerField(default=0, help_text="Cantidad entregada al paciente")
    fecha_dispensacion = models.DateTimeField(null=True, blank=True)
    lote_dispensado = models.CharField(max_length=50, blank=True, help_text="Lote del medicamento dispensado")
    
    # Control
    sustituido = models.BooleanField(default=False, help_text="Si fue sustituido por genérico")
    medicamento_sustituido = models.ForeignKey(Medicamento, on_delete=models.SET_NULL, null=True, blank=True,
                                               related_name='sustituciones',
                                               help_text="Medicamento genérico usado como sustituto")
    
    def __str__(self):
        return f"{self.medicamento.nombre_comercial} - {self.cantidad_prescrita} unidades"
    
    def completamente_dispensado(self):
        """Verifica si se dispensó la cantidad completa"""
        return self.cantidad_dispensada >= self.cantidad_prescrita
    
    def dispensar(self, cantidad, lote=""):
        """Registra la dispensación del medicamento"""
        if cantidad <= self.medicamento.stock_actual:
            self.cantidad_dispensada += cantidad
            self.fecha_dispensacion = timezone.now()
            if lote:
                self.lote_dispensado = lote
            self.save()
            
            # Actualizar stock del medicamento
            self.medicamento.stock_actual -= cantidad
            self.medicamento.save()
            
            # Registrar movimiento de inventario
            MovimientoInventario.objects.create(
                medicamento=self.medicamento,
                tipo_movimiento='salida',
                cantidad=cantidad,
                motivo=f'Dispensación receta {self.receta.codigo_receta}',
                usuario=self.receta.farmaceutico if self.receta.farmaceutico else None,
                lote_referencia=lote,
                stock_anterior=self.medicamento.stock_actual + cantidad,
                stock_nuevo=self.medicamento.stock_actual
            )
            
            return True
        return False
    
    class Meta:
        verbose_name = 'Detalle de Receta'
        verbose_name_plural = 'Detalles de Recetas'


class MovimientoInventario(models.Model):
    """Modelo para registrar todos los movimientos de inventario"""
    TIPO_MOVIMIENTO_CHOICES = [
        ('entrada', 'Entrada'),
        ('salida', 'Salida'),
        ('ajuste_positivo', 'Ajuste Positivo'),
        ('ajuste_negativo', 'Ajuste Negativo'),
        ('vencimiento', 'Por Vencimiento'),
        ('dañado', 'Por Daño'),
        ('devolucion', 'Devolución'),
    ]
    
    medicamento = models.ForeignKey(Medicamento, on_delete=models.CASCADE, related_name='movimientos')
    tipo_movimiento = models.CharField(max_length=20, choices=TIPO_MOVIMIENTO_CHOICES)
    cantidad = models.IntegerField(help_text="Cantidad del movimiento")
    motivo = models.TextField(help_text="Motivo del movimiento")
    fecha_movimiento = models.DateTimeField(auto_now_add=True)
    usuario = models.ForeignKey(Usuario, on_delete=models.SET_NULL, null=True, blank=True,
                                help_text="Usuario que realizó el movimiento")
    
    # Referencias adicionales
    lote_referencia = models.CharField(max_length=50, blank=True, help_text="Lote involucrado")
    proveedor = models.CharField(max_length=200, blank=True, help_text="Proveedor en caso de entrada")
    precio_unitario_momento = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True,
                                                   help_text="Precio unitario al momento del movimiento")
    
    # Control de stock
    stock_anterior = models.IntegerField(help_text="Stock antes del movimiento")
    stock_nuevo = models.IntegerField(help_text="Stock después del movimiento")
    
    # Documentos de respaldo
    numero_factura = models.CharField(max_length=50, blank=True, help_text="Número de factura o documento")
    observaciones = models.TextField(blank=True)
    
    def __str__(self):
        signo = '+' if self.tipo_movimiento in ['entrada', 'ajuste_positivo', 'devolucion'] else '-'
        return f"{self.medicamento.codigo} | {signo}{self.cantidad} | {self.get_tipo_movimiento_display()}"
    
    def es_entrada(self):
        """Verifica si es un movimiento de entrada al inventario"""
        return self.tipo_movimiento in ['entrada', 'ajuste_positivo', 'devolucion']
    
    def es_salida(self):
        """Verifica si es un movimiento de salida del inventario"""
        return self.tipo_movimiento in ['salida', 'ajuste_negativo', 'vencimiento', 'dañado']
    
    class Meta:
        verbose_name = 'Movimiento de Inventario'
        verbose_name_plural = 'Movimientos de Inventario'
        ordering = ['-fecha_movimiento']



