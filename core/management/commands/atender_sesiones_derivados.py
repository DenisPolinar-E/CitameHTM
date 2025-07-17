import random
from datetime import timedelta, time, datetime
from django.core.management.base import BaseCommand
from django.db import transaction
from django.utils import timezone
from core.models import Derivacion, Cita, TratamientoProgramado, SeguimientoSesion, RecetaMedica, DetalleReceta, Medicamento, HistorialMedico, Consultorio

class Command(BaseCommand):
    help = 'Atiende pacientes derivados a especialistas (derivaciones de 2024), programa y atiende sesiones, prescribe medicamentos y registra en historial médico.'

    def handle(self, *args, **options):
        random.seed(45)
        # Filtrar derivaciones cuya cita asociada sea de 2024
        derivaciones = list(Derivacion.objects.filter(
            cita_agendada=True,
            estado__in=['pendiente', 'usada'],
            citas__fecha__year=2024
        ).distinct())
        if len(derivaciones) < 250:
            self.stdout.write(self.style.WARNING(f"Solo hay {len(derivaciones)} derivaciones disponibles en 2024."))
        derivaciones_tratamiento = random.sample(derivaciones, min(250, len(derivaciones)))
        total_tratamientos = 0
        total_sesiones = 0
        total_recetas = 0
        total_historiales = 0
        medicamentos = list(Medicamento.objects.filter(stock_actual__gt=0))
        consultorios = list(Consultorio.objects.all())
        with transaction.atomic():
            for derivacion in derivaciones_tratamiento:
                # 1. Atender la cita de derivación
                cita_derivacion = Cita.objects.filter(derivacion=derivacion, fecha__year=2024).first()
                if not cita_derivacion:
                    continue
                if cita_derivacion.estado != 'atendida':
                    cita_derivacion.estado = 'atendida'
                    cita_derivacion.save()
                # 2. Crear tratamiento programado
                num_sesiones = random.randint(3, 10)
                frecuencia = random.randint(7, 10)
                fecha_inicio = cita_derivacion.fecha
                fecha_fin_estimada = fecha_inicio + timedelta(days=frecuencia*(num_sesiones-1))
                tratamiento = TratamientoProgramado.objects.create(
                    paciente=derivacion.paciente,
                    medico=cita_derivacion.medico,
                    diagnostico=derivacion.motivo,
                    cantidad_sesiones=num_sesiones,
                    sesiones_completadas=0,
                    frecuencia_dias=frecuencia,
                    fecha_inicio=fecha_inicio,
                    fecha_fin_estimada=fecha_fin_estimada,
                    estado='activo',
                    notas_seguimiento=f"Tratamiento por derivación: {derivacion.motivo}"
                )
                total_tratamientos += 1
                # 3. Programar y atender sesiones
                fecha_sesion = fecha_inicio
                sintomas_extra = [
                    'Dolor muscular', 'Náuseas', 'Fiebre', 'Cansancio', 'Mareos', 'Tos', 'Erupción cutánea',
                    'Inflamación', 'Ansiedad', 'Insomnio'
                ]
                nuevos_sintomas_paciente = set()
                for n in range(1, num_sesiones+1):
                    # Hora aleatoria entre 8:00 y 18:00
                    hora_inicio = time(hour=random.randint(8, 17), minute=random.choice([0, 15, 30, 45]))
                    hora_fin = (datetime.combine(fecha_sesion, hora_inicio) + timedelta(minutes=30)).time()
                    consultorio = random.choice(consultorios) if consultorios else None
                    # Limitar sesiones a 2024 si la fecha_sesion está fuera de 2024, pero permitir que se extiendan a 2025 si la frecuencia lo requiere
                    cita_sesion = Cita.objects.create(
                        paciente=tratamiento.paciente,
                        medico=tratamiento.medico,
                        consultorio=consultorio,
                        fecha=fecha_sesion,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        estado='confirmada',
                        motivo=f"Sesión {n} de tratamiento: {tratamiento.diagnostico}",
                    )
                    sesion = SeguimientoSesion.objects.create(
                        tratamiento=tratamiento,
                        numero_sesion=n,
                        fecha_programada=fecha_sesion,
                        estado='pendiente',
                        observaciones=f"Sesión {n} programada para seguimiento de tratamiento.",
                        cita=cita_sesion
                    )
                    # Atender la cita y la sesión
                    cita_sesion.estado = 'atendida'
                    cita_sesion.save()
                    sesion.estado = 'completada'
                    # Evolución realista
                    if n == 1:
                        evolucion = "Inicio de tratamiento, paciente motivado, sin reacciones adversas."
                    elif n == num_sesiones:
                        evolucion = "Alta médica, tratamiento completado con éxito."
                    else:
                        if random.random() < 0.2:  # 20% probabilidad de nuevo síntoma
                            sintoma_nuevo = random.choice([s for s in sintomas_extra if s not in nuevos_sintomas_paciente])
                            nuevos_sintomas_paciente.add(sintoma_nuevo)
                            evolucion = f"Aparece nuevo síntoma: {sintoma_nuevo}. Se ajusta medicación."
                        else:
                            evolucion = "Mejoría parcial, refiere dolor leve."
                    sesion.evolucion = evolucion
                    sesion.save()
                    # Prescripción de medicamentos (solo si la sesión es en 2024)
                    if (fecha_sesion.year == 2024) and (n == 1 or (n != num_sesiones and 'ajusta medicación' in evolucion)):
                        meds_disponibles = [m for m in medicamentos if m.stock_actual > 0]
                        if meds_disponibles:
                            num_meds = random.randint(1, min(3, len(meds_disponibles)))
                            meds_receta = random.sample(meds_disponibles, num_meds)
                            dt_cita = timezone.make_aware(datetime.combine(fecha_sesion, hora_inicio))
                            receta = RecetaMedica.objects.create(
                                cita=cita_sesion,
                                paciente=tratamiento.paciente,
                                medico=tratamiento.medico,
                                estado='dispensada',
                                observaciones_medico=f"Receta para sesión {n} de tratamiento.",
                                fecha_prescripcion=dt_cita
                            )
                            for med in meds_receta:
                                cantidad = random.randint(3, min(10, med.stock_actual))
                                DetalleReceta.objects.create(
                                    receta=receta,
                                    medicamento=med,
                                    cantidad_prescrita=cantidad,
                                    dosis="1 cada 8h",
                                    frecuencia="Cada 8 horas",
                                    duracion_dias=frecuencia,
                                    via_administracion="oral",
                                    instrucciones="Tomar según indicación médica.",
                                    cantidad_dispensada=cantidad,
                                    fecha_dispensacion=dt_cita,
                                )
                                med.stock_actual -= cantidad
                                med.save()
                            total_recetas += 1
                    # Registrar en historial médico (usar fecha de la sesión)
                    dt_historial = timezone.make_aware(datetime.combine(fecha_sesion, hora_inicio))
                    HistorialMedico.objects.create(
                        paciente=tratamiento.paciente,
                        fecha=dt_historial,
                        diagnostico=tratamiento.diagnostico,
                        tratamiento=f"Sesión {n}: {sesion.evolucion}",
                        observaciones=sesion.observaciones
                    )
                    total_historiales += 1
                    total_sesiones += 1
                    # Calcular fecha de la próxima sesión
                    fecha_sesion = fecha_sesion + timedelta(days=frecuencia)
        self.stdout.write(self.style.SUCCESS(f"Tratamientos creados: {total_tratamientos}"))
        self.stdout.write(self.style.SUCCESS(f"Sesiones programadas y atendidas: {total_sesiones}"))
        self.stdout.write(self.style.SUCCESS(f"Recetas generadas: {total_recetas}"))
        self.stdout.write(self.style.SUCCESS(f"Registros en historial médico: {total_historiales}")) 