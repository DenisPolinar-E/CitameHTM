from django.core.management.base import BaseCommand
from django.utils import timezone
from datetime import datetime
from core.models import RecetaMedica, DetalleReceta

class Command(BaseCommand):
    help = 'Actualiza fecha_prescripcion de recetas y fecha_dispensacion de detalles para que coincidan con la cita asociada (recetas de 2024 y 2025).'

    def handle(self, *args, **options):
        recetas_actualizadas = 0
        detalles_actualizados = 0
        warnings = 0
        recetas = RecetaMedica.objects.filter(cita__isnull=False, cita__fecha__year__in=[2024, 2025])
        for receta in recetas:
            cita = receta.cita
            if not cita or not cita.fecha or not cita.hora_inicio:
                self.stdout.write(self.style.WARNING(f"Receta {receta.id} sin cita o sin fecha/hora."))
                warnings += 1
                continue
            # Combinar fecha y hora de la cita
            dt_cita = timezone.make_aware(datetime.combine(cita.fecha, cita.hora_inicio))
            # Actualizar receta
            receta.fecha_prescripcion = dt_cita
            receta.save()
            recetas_actualizadas += 1
            # Actualizar detalles
            detalles = receta.detalles.all()
            for detalle in detalles:
                detalle.fecha_dispensacion = dt_cita
                detalle.save()
                detalles_actualizados += 1
        self.stdout.write(self.style.SUCCESS(f"Recetas actualizadas: {recetas_actualizadas}"))
        self.stdout.write(self.style.SUCCESS(f"Detalles de receta actualizados: {detalles_actualizados}"))
        if warnings:
            self.stdout.write(self.style.WARNING(f"Recetas con problemas: {warnings}")) 