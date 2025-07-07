import random
from datetime import timedelta, datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from core.models import Cita, RecetaMedica, DetalleReceta, Medicamento, Derivacion, Especialidad, Medico, Paciente
from django.utils import timezone

# Diagnósticos graves por especialidad (debe coincidir con los usados en el script anterior)
DIAGNOSTICOS_GRAVES = {
    'Emergencias': [
        'Infarto agudo de miocardio', 'Accidente cerebrovascular', 'Shock séptico', 'Traumatismo grave',
    ],
    'Medicina General': [
        'Diabetes descompensada', 'Insuficiencia renal aguda', 'Crisis hipertensiva',
    ],
    'Nutrición': [
        'Desnutrición severa', 'Obesidad mórbida', 'Anemia severa',
    ],
    'Obstetricia': [
        'Preeclampsia', 'Amenaza de aborto', 'Diabetes gestacional',
    ],
    'Odontología': [
        'Absceso dental', 'Periodontitis avanzada', 'Fractura dental',
    ],
    'Psicología': [
        'Depresión mayor', 'Trastorno de pánico', 'Riesgo suicida',
    ],
}

class Command(BaseCommand):
    help = 'Atiende las citas confirmadas de 2023, prescribe recetas y deriva pacientes según diagnóstico grave.'

    def handle(self, *args, **options):
        random.seed(43)
        citas_confirmadas = list(Cita.objects.filter(estado='confirmada', fecha__year=2023))
        total_atendidas = 0
        total_recetas = 0
        total_derivaciones = 0
        total_medicamentos_dispensados = 0
        medicamentos = list(Medicamento.objects.filter(stock_actual__gt=0))
        especialidades = {e.nombre: e for e in Especialidad.objects.all()}
        medicos_por_especialidad = {
            esp: list(Medico.objects.filter(especialidad=especialidades[esp]))
            for esp in especialidades
        }
        with transaction.atomic():
            for cita in citas_confirmadas:
                # 1. Marcar la cita como atendida
                cita.estado = 'atendida'
                cita.save()
                total_atendidas += 1
                # 2. Crear receta médica
                receta = RecetaMedica.objects.create(
                    cita=cita,
                    paciente=cita.paciente,
                    medico=cita.medico,
                    estado='dispensada',
                    observaciones_medico=f"Receta generada automáticamente para {cita.motivo}",
                )
                # Seleccionar 1-3 medicamentos distintos en stock
                meds_disponibles = [m for m in medicamentos if m.stock_actual > 0]
                if not meds_disponibles:
                    continue  # No hay medicamentos disponibles
                num_meds = random.randint(1, min(3, len(meds_disponibles)))
                meds_receta = random.sample(meds_disponibles, num_meds)
                for med in meds_receta:
                    cantidad = random.randint(1, min(5, med.stock_actual))
                    DetalleReceta.objects.create(
                        receta=receta,
                        medicamento=med,
                        cantidad_prescrita=cantidad,
                        dosis="1 cada 8h",
                        frecuencia="Cada 8 horas",
                        duracion_dias=random.randint(3, 10),
                        via_administracion="oral",
                        instrucciones="Tomar según indicación médica.",
                        cantidad_dispensada=cantidad,
                        fecha_dispensacion=timezone.now(),
                    )
                    med.stock_actual -= cantidad
                    med.save()
                    total_medicamentos_dispensados += cantidad
                total_recetas += 1
                # 3. Si requiere derivación (diagnóstico grave)
                especialidad_origen = cita.medico.especialidad.nombre
                requiere_derivacion = any(
                    grave.lower() in cita.motivo.lower() for grave in DIAGNOSTICOS_GRAVES.get(especialidad_origen, [])
                )
                if requiere_derivacion:
                    # Elegir especialidad destino diferente
                    especialidades_destino = [e for e in especialidades if e != especialidad_origen]
                    if not especialidades_destino:
                        continue  # No hay otra especialidad
                    especialidad_destino = random.choice(especialidades_destino)
                    medicos_destino = medicos_por_especialidad.get(especialidad_destino, [])
                    if not medicos_destino:
                        continue  # No hay médico en especialidad destino
                    medico_destino = random.choice(medicos_destino)
                    # Crear derivación
                    derivacion = Derivacion.objects.create(
                        paciente=cita.paciente,
                        medico_origen=cita.medico,
                        especialidad_destino=especialidades[especialidad_destino],
                        motivo=f"Derivación automática por diagnóstico: {cita.motivo}",
                        estado='pendiente',
                        cita_agendada=False,
                    )
                    # Crear nueva cita por derivación (fecha posterior a la original)
                    nueva_fecha = cita.fecha + timedelta(days=random.randint(7, 30))
                    consultorios = list(medico_destino.especialidad.consultorio_set.all()) if hasattr(medico_destino.especialidad, 'consultorio_set') else []
                    if not consultorios:
                        from core.models import Consultorio
                        consultorios = list(Consultorio.objects.all())
                    consultorio_destino = random.choice(consultorios) if consultorios else None
                    nueva_cita = Cita.objects.create(
                        paciente=cita.paciente,
                        medico=medico_destino,
                        consultorio=consultorio_destino,
                        fecha=nueva_fecha,
                        hora_inicio=cita.hora_inicio,
                        hora_fin=cita.hora_fin,
                        estado='confirmada',
                        motivo=f"Cita por derivación: {cita.motivo}",
                        derivacion=derivacion,
                    )
                    derivacion.cita_agendada = True
                    derivacion.save()
                    total_derivaciones += 1
        self.stdout.write(self.style.SUCCESS(f"Citas atendidas: {total_atendidas}"))
        self.stdout.write(self.style.SUCCESS(f"Recetas generadas: {total_recetas}"))
        self.stdout.write(self.style.SUCCESS(f"Medicamentos dispensados: {total_medicamentos_dispensados}"))
        self.stdout.write(self.style.SUCCESS(f"Derivaciones realizadas: {total_derivaciones}")) 