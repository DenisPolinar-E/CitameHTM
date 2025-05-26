import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos
from core.models import Especialidad, Medico, Usuario

# Listar todas las especialidades
print("=== ESPECIALIDADES DISPONIBLES ===")
especialidades = Especialidad.objects.all()
for esp in especialidades:
    print(f"ID: {esp.id}, Nombre: {esp.nombre}")

# Listar todos los médicos con sus especialidades
print("\n=== MÉDICOS REGISTRADOS ===")
medicos = Medico.objects.all()
if not medicos:
    print("No hay médicos registrados en el sistema.")
else:
    for med in medicos:
        try:
            print(f"ID: {med.id}, Nombre: {med.usuario.nombres} {med.usuario.apellidos}, Especialidad: {med.especialidad.nombre} (ID: {med.especialidad.id})")
        except Exception as e:
            print(f"Error al mostrar médico ID {med.id}: {str(e)}")

# Verificar médicos por especialidad específica
print("\n=== VERIFICACIÓN POR ESPECIALIDAD ===")
for esp in especialidades:
    medicos_esp = Medico.objects.filter(especialidad=esp)
    print(f"Especialidad: {esp.nombre} (ID: {esp.id}) - {medicos_esp.count()} médicos")
    for med in medicos_esp:
        try:
            print(f"  - ID: {med.id}, Nombre: {med.usuario.nombres} {med.usuario.apellidos}")
        except Exception as e:
            print(f"  - Error al mostrar médico ID {med.id}: {str(e)}")
