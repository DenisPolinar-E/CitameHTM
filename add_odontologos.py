import os
import django
from django.contrib.auth.hashers import make_password
from django.db import transaction

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Usuario, Medico, Especialidad, Rol

# Obtener el rol de médico
rol_medico, _ = Rol.objects.get_or_create(nombre='Medico')
print(f"Rol de Médico obtenido")

# Nombre de la especialidad
nombre_especialidad = "Odontología"
cantidad_a_crear = 3

# Datos para los odontólogos
odontologos = [
    {
        "nombres": "Carla",
        "apellidos": "Mendoza Vargas",
        "sexo": "F",
        "dni_base": "4001",
        "cmp_base": "30001"
    },
    {
        "nombres": "Sergio",
        "apellidos": "Paredes Gutiérrez",
        "sexo": "M",
        "dni_base": "4002",
        "cmp_base": "30002"
    },
    {
        "nombres": "Valeria",
        "apellidos": "Rojas Castillo",
        "sexo": "F",
        "dni_base": "4003",
        "cmp_base": "30003"
    }
]

try:
    # Buscar la especialidad
    try:
        especialidad = Especialidad.objects.get(nombre=nombre_especialidad)
        print(f"Especialidad encontrada: {nombre_especialidad} (ID: {especialidad.id})")
    except Especialidad.DoesNotExist:
        # Crear la especialidad si no existe
        especialidad = Especialidad.objects.create(
            nombre=nombre_especialidad,
            descripcion="Especialidad encargada del diagnóstico, tratamiento y prevención de enfermedades bucodentales.",
            acceso_directo=True
        )
        print(f"Especialidad creada: {nombre_especialidad} (ID: {especialidad.id})")
    
    # Crear odontólogos en una transacción
    with transaction.atomic():
        creados = 0
        
        for i, odontologo in enumerate(odontologos):
            try:
                # Generar DNI y CMP únicos
                dni = f"3{especialidad.id:02d}{odontologo['dni_base']}"
                cmp = f"CMP-{odontologo['cmp_base']}"
                
                # Generar email
                email = f"{odontologo['nombres'].lower()[0]}.{odontologo['apellidos'].split()[0].lower()}@hospitaltingomaria.gob.pe"
                
                # Crear usuario
                usuario = Usuario.objects.create(
                    username=dni,
                    nombres=odontologo['nombres'],
                    apellidos=odontologo['apellidos'],
                    dni=dni,
                    email=email,
                    password=make_password('Onepiece-2000'),
                    rol=rol_medico,
                    sexo=odontologo['sexo']
                )
                
                # Crear médico
                Medico.objects.create(
                    usuario=usuario,
                    cmp=cmp,
                    especialidad=especialidad
                )
                
                creados += 1
                print(f"Creado odontólogo {i+1}/{cantidad_a_crear}: Dr. {odontologo['nombres']} {odontologo['apellidos']} (DNI: {dni}, CMP: {cmp})")
                
            except Exception as e:
                print(f"Error al crear odontólogo {i+1}/{cantidad_a_crear}: {str(e)}")
        
        print(f"\nProceso completado: {creados} odontólogos creados.")
        print("Todos los odontólogos tienen la contraseña: Onepiece-2000")
        
except Exception as e:
    print(f"Error general: {str(e)}")
