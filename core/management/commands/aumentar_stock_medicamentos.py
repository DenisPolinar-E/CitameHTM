from django.core.management.base import BaseCommand
from core.models import Medicamento

class Command(BaseCommand):
    help = 'Aumenta el stock de todos los medicamentos existentes a 10,000 unidades.'

    def handle(self, *args, **options):
        medicamentos = Medicamento.objects.all()
        total_actualizados = 0
        for med in medicamentos:
            stock_anterior = med.stock_actual
            med.stock_actual = 10000
            med.save()
            self.stdout.write(f"{med.nombre_comercial} (ID: {med.id}): {stock_anterior} -> {med.stock_actual}")
            total_actualizados += 1
        self.stdout.write(self.style.SUCCESS(f"Total de medicamentos actualizados: {total_actualizados}")) 