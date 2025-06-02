from django.core.management.base import BaseCommand
from django.utils import timezone
from django.contrib.auth import get_user_model
from core.models import (
    Paciente, Medico, TratamientoProgramado, SeguimientoSesion, 
    Cita, Notificacion, Especialidad
)
from datetime import timedelta
import random

User = get_user_model()

class Command(BaseCommand):
    help = 'Genera datos de prueba para el sistema de seguimiento de pacientes'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=10,
            help='Cantidad de tratamientos a generar'
        )

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        
        # Verificar que existan pacientes y médicos
        pacientes = Paciente.objects.all()
        medicos = Medico.objects.all()
        
        if not pacientes.exists():
            self.stdout.write(self.style.ERROR('No hay pacientes registrados en el sistema'))
            return
        
        if not medicos.exists():
            self.stdout.write(self.style.ERROR('No hay médicos registrados en el sistema'))
            return
        
        # Diagnósticos de ejemplo
        diagnosticos = [
            "Hipertensión arterial",
            "Diabetes mellitus tipo 2",
            "Asma bronquial",
            "Artritis reumatoide",
            "Lumbalgia crónica",
            "Migraña crónica",
            "Hipotiroidismo",
            "Ansiedad generalizada",
            "Depresión mayor",
            "Enfermedad pulmonar obstructiva crónica",
            "Gastritis crónica",
            "Síndrome del intestino irritable",
            "Fibromialgia",
            "Osteoporosis",
            "Dermatitis atópica"
        ]
        
        # Notas de seguimiento de ejemplo
        notas_seguimiento = [
            "Paciente responde bien al tratamiento inicial.",
            "Se observa mejoría gradual en los síntomas.",
            "Paciente refiere disminución del dolor.",
            "Se ajusta dosis del medicamento por efectos secundarios leves.",
            "Paciente cumple con las indicaciones terapéuticas.",
            "Se recomienda continuar con el mismo esquema de tratamiento.",
            "Evolución favorable, se mantiene el plan terapéutico.",
            "Paciente presenta buena adherencia al tratamiento."
        ]
        
        # Observaciones de sesión de ejemplo
        observaciones_sesion = [
            "Paciente acude puntual a su cita.",
            "Paciente refiere mejoría en los síntomas.",
            "Se realiza ajuste en la medicación.",
            "Paciente presenta efectos secundarios leves.",
            "Se refuerzan indicaciones terapéuticas.",
            "Paciente cumple parcialmente con las indicaciones.",
            "Se observa mejoría clínica.",
            "Se solicitan exámenes complementarios."
        ]
        
        # Evolución de sesión de ejemplo
        evoluciones_sesion = [
            "Evolución favorable. Paciente refiere disminución de los síntomas.",
            "Mejoría parcial. Se ajusta esquema terapéutico.",
            "Evolución satisfactoria. Se mantiene el tratamiento actual.",
            "Respuesta adecuada al tratamiento. Se continúa con el mismo esquema.",
            "Evolución lenta pero favorable. Se refuerzan medidas terapéuticas.",
            "Buena respuesta al tratamiento. Se disminuye dosis del medicamento.",
            "Evolución dentro de lo esperado. Se mantiene vigilancia.",
            "Mejoría significativa. Se plantea reducir frecuencia de sesiones."
        ]
        
        # Generar tratamientos
        tratamientos_creados = 0
        for _ in range(cantidad):
            # Seleccionar paciente y médico aleatorios
            paciente = random.choice(pacientes)
            medico = random.choice(medicos)
            
            # Datos del tratamiento
            diagnostico = random.choice(diagnosticos)
            cantidad_sesiones = random.randint(3, 12)
            frecuencia_dias = random.choice([7, 14, 21, 30])
            
            # Fecha de inicio (entre 90 días atrás y hoy)
            dias_atras = random.randint(0, 90)
            fecha_inicio = timezone.now().date() - timedelta(days=dias_atras)
            
            # Estado del tratamiento (80% activos, 10% completados, 10% cancelados)
            estado_rand = random.random()
            if estado_rand < 0.8:
                estado = 'activo'
                sesiones_completadas = random.randint(0, cantidad_sesiones - 1)
            elif estado_rand < 0.9:
                estado = 'completado'
                sesiones_completadas = cantidad_sesiones
            else:
                estado = 'cancelado'
                sesiones_completadas = random.randint(0, cantidad_sesiones - 1)
            
            # Crear tratamiento
            tratamiento = TratamientoProgramado.objects.create(
                paciente=paciente,
                medico=medico,
                diagnostico=diagnostico,
                cantidad_sesiones=cantidad_sesiones,
                sesiones_completadas=sesiones_completadas,
                frecuencia_dias=frecuencia_dias,
                fecha_inicio=fecha_inicio,
                estado=estado,
                notas_seguimiento=random.choice(notas_seguimiento)
            )
            
            # Crear sesiones de seguimiento
            fecha_sesion = fecha_inicio
            for i in range(1, cantidad_sesiones + 1):
                # Determinar estado de la sesión
                if i <= sesiones_completadas:
                    sesion_estado = 'completada'
                elif estado == 'cancelado':
                    sesion_estado = 'cancelada'
                elif random.random() < 0.7:  # 70% de probabilidad de tener cita programada
                    sesion_estado = 'programada'
                else:
                    sesion_estado = 'pendiente'
                
                # Crear sesión
                sesion = SeguimientoSesion.objects.create(
                    tratamiento=tratamiento,
                    numero_sesion=i,
                    fecha_programada=fecha_sesion,
                    estado=sesion_estado,
                    observaciones=random.choice(observaciones_sesion) if sesion_estado == 'completada' else '',
                    evolucion=random.choice(evoluciones_sesion) if sesion_estado == 'completada' else ''
                )
                
                # Si la sesión está programada o completada, crear una cita asociada
                if sesion_estado in ['programada', 'completada']:
                    # Hora aleatoria entre 8:00 y 16:00
                    hora = random.randint(8, 16)
                    minuto = random.choice([0, 15, 30, 45])
                    
                    estado_cita = 'atendida' if sesion_estado == 'completada' else 'confirmada'
                    
                    # Crear cita
                    cita = Cita.objects.create(
                        paciente=paciente,
                        medico=medico,
                        fecha=fecha_sesion,
                        hora_inicio=f"{hora:02d}:{minuto:02d}",
                        hora_fin=f"{hora:02d}:{minuto+30:02d}",
                        motivo=f"Sesión {i} - {diagnostico}",
                        estado=estado_cita,
                        tipo='seguimiento'
                    )
                    
                    # Asociar cita a la sesión
                    sesion.cita = cita
                    sesion.save()
                
                # Avanzar a la siguiente fecha de sesión
                fecha_sesion = fecha_sesion + timedelta(days=frecuencia_dias)
            
            # Crear notificación para el paciente
            Notificacion.objects.create(
                usuario=paciente.usuario,
                mensaje=f"Se ha programado un tratamiento: {diagnostico}",
                tipo='informacion',
                leida=random.choice([True, False]),
                importante=True,
                url_redireccion='/mis-tratamientos/',
                objeto_relacionado='tratamiento',
                objeto_id=tratamiento.id
            )
            
            tratamientos_creados += 1
            
        self.stdout.write(
            self.style.SUCCESS(f'Se han creado {tratamientos_creados} tratamientos con sus respectivas sesiones de seguimiento')
        )
