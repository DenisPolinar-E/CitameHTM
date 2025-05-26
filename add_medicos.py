import os
import django
import random
from django.contrib.auth.hashers import make_password

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Usuario, Medico, Especialidad, Rol

# Obtener el rol de médico o crearlo si no existe
rol_medico, created = Rol.objects.get_or_create(nombre='Medico')
if created:
    print("Rol de Médico creado")

# Lista de médicos a crear
medicos = [
    # Neonatología
    {
        'nombres': 'Carlos', 'apellidos': 'Mendoza Vargas',
        'dni': '10456789', 'email': 'carlos.mendoza@hospital.gob.pe',
        'especialidad': 'Neonatología', 'cmp': 'CMP-45678'
    },
    # Ginecología
    {
        'nombres': 'María', 'apellidos': 'Sánchez Torres',
        'dni': '10567890', 'email': 'maria.sanchez@hospital.gob.pe',
        'especialidad': 'Ginecología', 'cmp': 'CMP-56789'
    },
    # Obstetricia
    {
        'nombres': 'Laura', 'apellidos': 'Gutiérrez Paz',
        'dni': '10678901', 'email': 'laura.gutierrez@hospital.gob.pe',
        'especialidad': 'Obstetricia', 'cmp': 'CMP-67890'
    },
    # Emergencias
    {
        'nombres': 'Roberto', 'apellidos': 'Díaz Mendoza',
        'dni': '10789012', 'email': 'roberto.diaz@hospital.gob.pe',
        'especialidad': 'Emergencias', 'cmp': 'CMP-78901'
    },
    # Cuidados Críticos
    {
        'nombres': 'Patricia', 'apellidos': 'Ortega Ramírez',
        'dni': '10890123', 'email': 'patricia.ortega@hospital.gob.pe',
        'especialidad': 'Cuidados Críticos', 'cmp': 'CMP-89012'
    },
    # Anestesiología
    {
        'nombres': 'Javier', 'apellidos': 'Ramos Castillo',
        'dni': '10901234', 'email': 'javier.ramos@hospital.gob.pe',
        'especialidad': 'Anestesiología', 'cmp': 'CMP-90123'
    },
    # Patología Clínica
    {
        'nombres': 'Silvia', 'apellidos': 'Morales Vega',
        'dni': '11012345', 'email': 'silvia.morales@hospital.gob.pe',
        'especialidad': 'Patología Clínica', 'cmp': 'CMP-01234'
    },
    # Anatomía Patológica
    {
        'nombres': 'Ricardo', 'apellidos': 'Fuentes Silva',
        'dni': '11123456', 'email': 'ricardo.fuentes@hospital.gob.pe',
        'especialidad': 'Anatomía Patológica', 'cmp': 'CMP-12345'
    },
    # Diagnóstico por Imágenes
    {
        'nombres': 'Carmen', 'apellidos': 'Rojas Medina',
        'dni': '11234567', 'email': 'carmen.rojas@hospital.gob.pe',
        'especialidad': 'Diagnóstico por Imágenes', 'cmp': 'CMP-23456'
    },
    # Nutrición
    {
        'nombres': 'Miguel', 'apellidos': 'Torres Ríos',
        'dni': '11345678', 'email': 'miguel.torres@hospital.gob.pe',
        'especialidad': 'Nutrición', 'cmp': 'CMP-34567'
    },
    # Psicología
    {
        'nombres': 'Ana', 'apellidos': 'Flores Castro',
        'dni': '11456789', 'email': 'ana.flores@hospital.gob.pe',
        'especialidad': 'Psicología', 'cmp': 'CMP-45678'
    },
    # Medicina General
    {
        'nombres': 'Jorge', 'apellidos': 'Paredes Ruiz',
        'dni': '11567890', 'email': 'jorge.paredes@hospital.gob.pe',
        'especialidad': 'Medicina General', 'cmp': 'CMP-56789'
    },
    # Cardiología
    {
        'nombres': 'Lucía', 'apellidos': 'Vargas Campos',
        'dni': '11678901', 'email': 'lucia.vargas@hospital.gob.pe',
        'especialidad': 'Cardiología', 'cmp': 'CMP-67890'
    },
    # Neumología
    {
        'nombres': 'Daniel', 'apellidos': 'Herrera Soto',
        'dni': '11789012', 'email': 'daniel.herrera@hospital.gob.pe',
        'especialidad': 'Neumología', 'cmp': 'CMP-78901'
    },
    # Gastroenterología
    {
        'nombres': 'Mónica', 'apellidos': 'Castillo Vega',
        'dni': '11890123', 'email': 'monica.castillo@hospital.gob.pe',
        'especialidad': 'Gastroenterología', 'cmp': 'CMP-89012'
    },
    # Dermatología
    {
        'nombres': 'Fernando', 'apellidos': 'Ríos Mendoza',
        'dni': '11901234', 'email': 'fernando.rios@hospital.gob.pe',
        'especialidad': 'Dermatología', 'cmp': 'CMP-90123'
    },
    # Reumatología
    {
        'nombres': 'Elena', 'apellidos': 'Medina Ortega',
        'dni': '12012345', 'email': 'elena.medina@hospital.gob.pe',
        'especialidad': 'Reumatología', 'cmp': 'CMP-01234'
    },
    # Cirugía General
    {
        'nombres': 'Raúl', 'apellidos': 'Castro Díaz',
        'dni': '12123456', 'email': 'raul.castro@hospital.gob.pe',
        'especialidad': 'Cirugía General', 'cmp': 'CMP-12345'
    },
    # Cirugía de Cabeza y Cuello
    {
        'nombres': 'Gabriela', 'apellidos': 'Soto Ramos',
        'dni': '12234567', 'email': 'gabriela.soto@hospital.gob.pe',
        'especialidad': 'Cirugía de Cabeza y Cuello', 'cmp': 'CMP-23456'
    },
    # Cirugía de Tórax
    {
        'nombres': 'Héctor', 'apellidos': 'Vega Fuentes',
        'dni': '12345678', 'email': 'hector.vega@hospital.gob.pe',
        'especialidad': 'Cirugía de Tórax', 'cmp': 'CMP-34567'
    }
]

# Contador para médicos creados
creados = 0
actualizados = 0

# Crear o actualizar médicos
for medico_data in medicos:
    try:
        # Buscar la especialidad
        try:
            especialidad = Especialidad.objects.get(nombre=medico_data['especialidad'])
        except Especialidad.DoesNotExist:
            print(f"Error: Especialidad '{medico_data['especialidad']}' no encontrada. Saltando médico.")
            continue
        
        # Crear o actualizar usuario
        usuario, created_user = Usuario.objects.update_or_create(
            dni=medico_data['dni'],
            defaults={
                'username': medico_data['dni'],
                'nombres': medico_data['nombres'],
                'apellidos': medico_data['apellidos'],
                'email': medico_data['email'],
                'password': make_password('password123'),  # Contraseña por defecto
                'rol': rol_medico
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
        print(f"Error al crear médico {medico_data['nombres']} {medico_data['apellidos']}: {str(e)}")

print(f"\nProceso completado: {creados} médicos creados, {actualizados} actualizados.")
