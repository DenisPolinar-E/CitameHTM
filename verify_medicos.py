import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos
from core.models import Especialidad, Medico

# Contar médicos por especialidad
print("=== MÉDICOS POR ESPECIALIDAD ===")
especialidades = Especialidad.objects.all().order_by('nombre')

total_medicos = 0
for esp in especialidades:
    medicos_count = Medico.objects.filter(especialidad=esp).count()
    total_medicos += medicos_count
    print(f"{esp.nombre}: {medicos_count} médicos")

print(f"\nTotal de médicos en el sistema: {total_medicos}")
