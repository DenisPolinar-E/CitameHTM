from django import forms
from django.contrib.auth.forms import UserCreationForm, AuthenticationForm
from django.core.exceptions import ValidationError
from datetime import datetime, time
from .models import Usuario, Paciente, Medico, Cita, Derivacion, HistorialMedico, TratamientoProgramado, DisponibilidadMedica, DatosAntropometricos, DIAS_SEMANA_CHOICES, TIPO_TURNO_CHOICES

class RegistroPacienteForm(forms.ModelForm):
    """Formulario para el registro de usuarios con diferentes roles"""
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)
    password2 = forms.CharField(label='Confirmar contraseña', widget=forms.PasswordInput)
    
    class Meta:
        model = Usuario
        fields = ['nombres', 'apellidos', 'dni', 'email', 'fecha_nacimiento', 'sexo', 'telefono', 'direccion']
        widgets = {
            'fecha_nacimiento': forms.DateInput(attrs={'type': 'date'}),
        }
    
    def clean_password2(self):
        # Verificar que las contraseñas coincidan
        password = self.cleaned_data.get('password')
        password2 = self.cleaned_data.get('password2')
        if password and password2 and password != password2:
            raise forms.ValidationError('Las contraseñas no coinciden')
        return password2
    
    def clean_dni(self):
        # Verificar que el DNI tenga 8 dígitos
        dni = self.cleaned_data.get('dni')
        if dni and (len(dni) != 8 or not dni.isdigit()):
            raise forms.ValidationError('El DNI debe tener 8 dígitos numéricos')
        
        # Verificar que el DNI no esté registrado
        if Usuario.objects.filter(dni=dni).exists():
            raise forms.ValidationError('Este DNI ya está registrado en el sistema')
        
        return dni

class LoginForm(AuthenticationForm):
    """Formulario personalizado para inicio de sesión"""
    username = forms.CharField(label='DNI', widget=forms.TextInput(attrs={'autofocus': True}))
    password = forms.CharField(label='Contraseña', widget=forms.PasswordInput)

class CitaForm(forms.ModelForm):
    """Formulario para crear/editar citas"""
    class Meta:
        model = Cita
        fields = ['paciente', 'medico', 'consultorio', 'fecha', 'hora_inicio', 'hora_fin', 'motivo']
        widgets = {
            'fecha': forms.DateInput(attrs={'type': 'date'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time'}),
        }
    
    def clean(self):
        cleaned_data = super().clean()
        medico = cleaned_data.get('medico')
        fecha = cleaned_data.get('fecha')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        # Verificar que la hora de fin sea posterior a la hora de inicio
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            raise forms.ValidationError('La hora de fin debe ser posterior a la hora de inicio')
        
        # Verificar disponibilidad del médico
        if medico and fecha and hora_inicio and hora_fin:
            # Verificar si hay citas que se solapan
            citas_solapadas = Cita.objects.filter(
                medico=medico,
                fecha=fecha,
                estado__in=['pendiente', 'confirmada']
            ).exclude(pk=self.instance.pk if self.instance.pk else None)
            
            for cita in citas_solapadas:
                if (hora_inicio < cita.hora_fin and hora_fin > cita.hora_inicio):
                    raise forms.ValidationError(f'El médico ya tiene una cita programada en ese horario ({cita.hora_inicio} - {cita.hora_fin})')
        
        return cleaned_data

class DerivacionForm(forms.ModelForm):
    """Formulario para crear derivaciones"""
    class Meta:
        model = Derivacion
        fields = ['paciente', 'especialidad_destino', 'motivo', 'vigencia_dias']
        widgets = {
            'motivo': forms.Textarea(attrs={'rows': 4}),
        }

class HistorialMedicoForm(forms.ModelForm):
    """Formulario para registrar historial médico"""
    class Meta:
        model = HistorialMedico
        fields = ['diagnostico', 'tratamiento', 'observaciones']
        widgets = {
            'diagnostico': forms.Textarea(attrs={'rows': 4}),
            'tratamiento': forms.Textarea(attrs={'rows': 4}),
            'observaciones': forms.Textarea(attrs={'rows': 4}),
        }

class TratamientoProgramadoForm(forms.ModelForm):
    """Formulario para programar tratamientos con múltiples sesiones"""
    class Meta:
        model = TratamientoProgramado
        fields = ['paciente', 'diagnostico', 'cantidad_sesiones', 'frecuencia_dias', 'fecha_inicio']
        widgets = {
            'fecha_inicio': forms.DateInput(attrs={'type': 'date'}),
            'diagnostico': forms.Textarea(attrs={'rows': 4}),
        }


class DatosAntropometricosForm(forms.ModelForm):
    """Formulario para registrar datos antropométricos del paciente"""
    class Meta:
        model = DatosAntropometricos
        fields = ['peso', 'talla']
        widgets = {
            'peso': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.01', 'min': '0', 'placeholder': 'Peso en kg'}),
            'talla': forms.NumberInput(attrs={'class': 'form-control', 'step': '0.1', 'min': '0', 'placeholder': 'Talla en cm'}),
        }
        
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['peso'].help_text = 'Ingrese el peso en kilogramos (ej. 70.5)'
        self.fields['talla'].help_text = 'Ingrese la talla en centímetros (ej. 175.0)'

class JustificarInasistenciaForm(forms.ModelForm):
    """Formulario para justificar inasistencias"""
    class Meta:
        model = Cita
        fields = ['motivo_no_asistencia', 'fue_justificada']
        widgets = {
            'motivo_no_asistencia': forms.Textarea(attrs={'rows': 4}),
        }

class DisponibilidadMedicaForm(forms.ModelForm):
    """Formulario para gestionar la disponibilidad médica"""
    # Campos adicionales para mejor experiencia de usuario
    tipo_disponibilidad = forms.ChoiceField(
        choices=[
            ('regular', 'Disponibilidad Regular (Día de semana)'),
            ('especial', 'Disponibilidad Especial (Fecha específica)')
        ],
        widget=forms.RadioSelect,
        initial='regular',
        required=True
    )
    
    class Meta:
        model = DisponibilidadMedica
        fields = ['tipo_disponibilidad', 'dia_semana', 'fecha_especial', 'hora_inicio', 'hora_fin', 'tipo_turno']
        widgets = {
            'dia_semana': forms.Select(attrs={'class': 'form-select'}),
            'fecha_especial': forms.DateInput(attrs={'type': 'date', 'class': 'form-control'}),
            'hora_inicio': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'hora_fin': forms.TimeInput(attrs={'type': 'time', 'class': 'form-control'}),
            'tipo_turno': forms.Select(attrs={'class': 'form-select'}),
        }
    
    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.fields['dia_semana'].required = False
        self.fields['fecha_especial'].required = False
        
        # Si es una instancia existente, establecer el tipo de disponibilidad
        if self.instance.pk:
            if self.instance.fecha_especial:
                self.fields['tipo_disponibilidad'].initial = 'especial'
            else:
                self.fields['tipo_disponibilidad'].initial = 'regular'
    
    def clean(self):
        cleaned_data = super().clean()
        tipo_disponibilidad = cleaned_data.get('tipo_disponibilidad')
        dia_semana = cleaned_data.get('dia_semana')
        fecha_especial = cleaned_data.get('fecha_especial')
        hora_inicio = cleaned_data.get('hora_inicio')
        hora_fin = cleaned_data.get('hora_fin')
        
        # Validar que se haya seleccionado día de semana o fecha específica según el tipo
        if tipo_disponibilidad == 'regular' and not dia_semana:
            self.add_error('dia_semana', 'Debe seleccionar un día de la semana para disponibilidad regular')
        
        if tipo_disponibilidad == 'especial' and not fecha_especial:
            self.add_error('fecha_especial', 'Debe seleccionar una fecha específica')
        
        # Si es fecha específica, validar que no sea en el pasado
        if fecha_especial and fecha_especial < datetime.now().date():
            self.add_error('fecha_especial', 'La fecha no puede ser en el pasado')
        
        # Validar que la hora de fin sea posterior a la hora de inicio
        if hora_inicio and hora_fin and hora_inicio >= hora_fin:
            self.add_error('hora_fin', 'La hora de fin debe ser posterior a la hora de inicio')
        
        # Limpiar campos según el tipo de disponibilidad
        if tipo_disponibilidad == 'regular':
            cleaned_data['fecha_especial'] = None
        else:  # especial
            cleaned_data['dia_semana'] = None
        
        return cleaned_data
