import os
import django
from django.contrib.auth.hashers import make_password

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Usuario, Medico, Especialidad, Rol

# Obtener el rol de médico
rol_medico, _ = Rol.objects.get_or_create(nombre='Medico')
print(f"Rol de Médico obtenido")

# Lista de médicos a crear (solo 5 para probar)
medicos_test = [
    # Neonatología - 1 médico
    {"especialidad": "Neonatología", "nombres": "Carlos", "apellidos": "Mendoza Vargas", "dni": "10456789", "cmp": "CMP-45678", "genero": "M"},
    
    # Ginecología - 1 médico
    {"especialidad": "Ginecología", "nombres": "Laura", "apellidos": "Sánchez Torres", "dni": "10456791", "cmp": "CMP-45680", "genero": "F"},
    
    # Obstetricia - 1 obstetra
    {"especialidad": "Obstetricia", "nombres": "Silvia", "apellidos": "Díaz Mendoza", "dni": "10456794", "cmp": "CMP-45683", "genero": "F"},
    
    # Emergencias - 1 médico
    {"especialidad": "Emergencias", "nombres": "Roberto", "apellidos": "Rojas Medina", "dni": "10456799", "cmp": "CMP-45688", "genero": "M"},
    
    # Medicina General - 1 médico
    {"especialidad": "Medicina General", "nombres": "José", "apellidos": "Chávez Espinoza", "dni": "10456822", "cmp": "CMP-45711", "genero": "M"}
]

# Contador para médicos creados
creados = 0
actualizados = 0
errores = 0

# Crear o actualizar médicos
for medico_data in medicos_test:
    try:
        # Buscar la especialidad
        try:
            especialidad = Especialidad.objects.get(nombre=medico_data['especialidad'])
            print(f"Especialidad encontrada: {medico_data['especialidad']}")
        except Especialidad.DoesNotExist:
            print(f"Error: Especialidad '{medico_data['especialidad']}' no encontrada. Saltando médico.")
            errores += 1
            continue
        
        # Crear o actualizar usuario
        email = f"{medico_data['nombres'].lower()[0]}.{medico_data['apellidos'].split()[0].lower()}@hospitaltingomaria.gob.pe"
        
        usuario, created_user = Usuario.objects.update_or_create(
            dni=medico_data['dni'],
            defaults={
                'username': medico_data['dni'],
                'nombres': medico_data['nombres'],
                'apellidos': medico_data['apellidos'],
                'email': email,
                'password': make_password('Onepiece-2000'),  # Contraseña especificada
                'rol': rol_medico,
                'genero': medico_data['genero']
            }
        )
        
        # Crear o actualizar médico
        medico, created_medico = Medico.objects.update_or_create(
            usuario=usuario,
            defaults={
                'cmp': medico_data['cmp'],
                'especialidad': especialidad
            }
        )
        
        if created_user or created_medico:
            creados += 1
            print(f"Creado médico: Dr. {usuario.nombres} {usuario.apellidos} - {especialidad.nombre}")
        else:
            actualizados += 1
            print(f"Actualizado médico: Dr. {usuario.nombres} {usuario.apellidos} - {especialidad.nombre}")
            
    except Exception as e:
        errores += 1
        print(f"Error al crear médico {medico_data['nombres']} {medico_data['apellidos']}: {str(e)}")

print(f"\nProceso completado: {creados} médicos creados, {actualizados} actualizados, {errores} errores.")
print("Todos los médicos tienen la contraseña: Onepiece-2000")
