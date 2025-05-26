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

# Verificar médicos existentes por especialidad
print("=== MÉDICOS EXISTENTES VS REQUERIDOS ===")
print(f"{'ESPECIALIDAD':<30} {'EXISTENTES':<10} {'REQUERIDOS':<10} {'FALTANTES':<10}")
print("-" * 60)

total_existentes = 0
total_requeridos = 0
total_faltantes = 0

# Crear un diccionario para almacenar la cantidad faltante por especialidad
medicos_faltantes = {}

for nombre_especialidad, cantidad_requerida in especialidades_requeridas.items():
    try:
        especialidad = Especialidad.objects.get(nombre=nombre_especialidad)
        cantidad_existente = Medico.objects.filter(especialidad=especialidad).count()
        
        faltantes = max(0, cantidad_requerida - cantidad_existente)
        
        # Guardar la cantidad faltante para cada especialidad
        if faltantes > 0:
            medicos_faltantes[nombre_especialidad] = faltantes
        
        total_existentes += cantidad_existente
        total_requeridos += cantidad_requerida
        total_faltantes += faltantes
        
        print(f"{nombre_especialidad:<30} {cantidad_existente:<10} {cantidad_requerida:<10} {faltantes:<10}")
    except Especialidad.DoesNotExist:
        print(f"{nombre_especialidad:<30} {'N/A':<10} {cantidad_requerida:<10} {cantidad_requerida:<10}")
        total_requeridos += cantidad_requerida
        total_faltantes += cantidad_requerida
        
        # Guardar la cantidad faltante para cada especialidad
        medicos_faltantes[nombre_especialidad] = cantidad_requerida

print("-" * 60)
print(f"{'TOTAL':<30} {total_existentes:<10} {total_requeridos:<10} {total_faltantes:<10}")

# Guardar los médicos faltantes en un archivo para usarlo en el script de creación
with open('medicos_faltantes.py', 'w') as f:
    f.write("# Médicos faltantes por especialidad\n")
    f.write("medicos_faltantes = {\n")
    for especialidad, cantidad in medicos_faltantes.items():
        f.write(f"    \"{especialidad}\": {cantidad},\n")
    f.write("}\n")
