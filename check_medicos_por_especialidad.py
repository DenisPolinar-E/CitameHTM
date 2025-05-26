import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos
from core.models import Especialidad, Medico

# Definir la cantidad requerida de médicos por especialidad
especialidades_requeridas = {
    "Neonatología": 2,
    "Ginecología": 3,
    "Obstetricia": 5,
    "Emergencias": 6,
    "Cuidados Críticos": 2,
    "Anestesiología": 3,
    "Patología Clínica": 2,
    "Anatomía Patológica": 1,
    "Diagnóstico por Imágenes": 2,
    "Nutrición": 1,
    "Psicología": 2,
    "Servicio Social": 2,
    "Farmacia": 1,
    "Rehabilitación": 1,
    "Medicina General": 10,
    "Cardiología": 1,
    "Neumología": 1,
    "Gastroenterología": 1,
    "Dermatología": 1,
    "Reumatología": 1,
    "Cirugía General": 3,
    "Cirugía de Cabeza y Cuello": 1,
    "Cirugía de Tórax": 1,
    "Cirugía Digestiva": 1,
    "Cirugía Proctológica": 1,
    "Medicina Física y Rehabilitación": 1
}

# Obtener todas las especialidades
especialidades = Especialidad.objects.all().order_by('nombre')

print("=== MÉDICOS POR ESPECIALIDAD (ACTUAL VS REQUERIDO) ===")
print("Especialidad | Actuales | Requeridos | Faltantes")
print("-" * 60)

total_actuales = 0
total_requeridos = 0
total_faltantes = 0

for esp in especialidades:
    # Contar médicos actuales para esta especialidad
    medicos_count = Medico.objects.filter(especialidad=esp).count()
    total_actuales += medicos_count
    
    # Obtener cantidad requerida (si existe en el diccionario)
    requeridos = especialidades_requeridas.get(esp.nombre, 0)
    total_requeridos += requeridos
    
    # Calcular faltantes
    faltantes = max(0, requeridos - medicos_count)
    total_faltantes += faltantes
    
    # Mostrar información
    print(f"{esp.nombre:<25} | {medicos_count:^8} | {requeridos:^10} | {faltantes:^8}")

print("-" * 60)
print(f"TOTAL                     | {total_actuales:^8} | {total_requeridos:^10} | {total_faltantes:^8}")

# Mostrar detalles de los médicos existentes
print("\n=== DETALLE DE MÉDICOS EXISTENTES ===")
for esp in especialidades:
    medicos = Medico.objects.filter(especialidad=esp)
    if medicos:
        print(f"\nEspecialidad: {esp.nombre} ({medicos.count()} médicos)")
        for med in medicos:
            print(f"  - Dr. {med.usuario.nombres} {med.usuario.apellidos} (DNI: {med.usuario.dni}, CMP: {med.cmp})")
