import os
import django

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Especialidad

# Lista de especialidades con sus descripciones
especialidades = [
    {
        'nombre': 'Neonatología',
        'descripcion': 'Especialidad médica que se ocupa de la atención y tratamiento de los recién nacidos hasta los 28 días de vida.',
        'acceso_directo': False
    },
    {
        'nombre': 'Ginecología',
        'descripcion': 'Especialidad médica que se ocupa de la salud del sistema reproductor femenino.',
        'acceso_directo': False
    },
    {
        'nombre': 'Obstetricia',
        'descripcion': 'Especialidad médica que se ocupa del embarazo, parto y puerperio.',
        'acceso_directo': False
    },
    {
        'nombre': 'Emergencias',
        'descripcion': 'Atención médica inmediata para pacientes con condiciones que requieren intervención urgente.',
        'acceso_directo': False
    },
    {
        'nombre': 'Cuidados Críticos',
        'descripcion': 'Atención especializada para pacientes en estado crítico que requieren monitoreo intensivo.',
        'acceso_directo': False
    },
    {
        'nombre': 'Anestesiología',
        'descripcion': 'Especialidad médica dedicada a la administración de anestesia y manejo del dolor.',
        'acceso_directo': False
    },
    {
        'nombre': 'Patología Clínica',
        'descripcion': 'Especialidad médica que estudia las enfermedades a través del análisis de fluidos corporales y tejidos.',
        'acceso_directo': False
    },
    {
        'nombre': 'Anatomía Patológica',
        'descripcion': 'Especialidad médica que estudia las alteraciones estructurales de órganos y tejidos.',
        'acceso_directo': False
    },
    {
        'nombre': 'Diagnóstico por Imágenes',
        'descripcion': 'Especialidad médica que utiliza técnicas de imagen para diagnosticar enfermedades.',
        'acceso_directo': False
    },
    {
        'nombre': 'Nutrición',
        'descripcion': 'Especialidad que se ocupa de la alimentación y su relación con la salud.',
        'acceso_directo': False
    },
    {
        'nombre': 'Psicología',
        'descripcion': 'Especialidad que se ocupa de la salud mental y el bienestar emocional de los pacientes.',
        'acceso_directo': True  # Única especialidad con acceso directo
    },
    {
        'nombre': 'Servicio Social',
        'descripcion': 'Área que brinda apoyo social y orientación a pacientes y familiares.',
        'acceso_directo': False
    },
    {
        'nombre': 'Farmacia',
        'descripcion': 'Servicio encargado de la dispensación y control de medicamentos.',
        'acceso_directo': False
    },
    {
        'nombre': 'Rehabilitación',
        'descripcion': 'Especialidad que ayuda a recuperar funciones físicas perdidas o disminuidas.',
        'acceso_directo': False
    },
    {
        'nombre': 'Medicina General',
        'descripcion': 'Atención médica integral y continua para pacientes de todas las edades.',
        'acceso_directo': False
    },
    {
        'nombre': 'Cardiología',
        'descripcion': 'Especialidad médica que se ocupa de las enfermedades del corazón y del sistema circulatorio.',
        'acceso_directo': False
    },
    {
        'nombre': 'Neumología',
        'descripcion': 'Especialidad médica que se ocupa de las enfermedades del sistema respiratorio.',
        'acceso_directo': False
    },
    {
        'nombre': 'Gastroenterología',
        'descripcion': 'Especialidad médica que se ocupa de las enfermedades del aparato digestivo.',
        'acceso_directo': False
    },
    {
        'nombre': 'Dermatología',
        'descripcion': 'Especialidad médica que se ocupa de las enfermedades de la piel.',
        'acceso_directo': False
    },
    {
        'nombre': 'Reumatología',
        'descripcion': 'Especialidad médica que se ocupa de las enfermedades del sistema musculoesquelético.',
        'acceso_directo': False
    },
    {
        'nombre': 'Cirugía General',
        'descripcion': 'Especialidad quirúrgica que abarca una amplia variedad de procedimientos quirúrgicos.',
        'acceso_directo': False
    },
    {
        'nombre': 'Cirugía de Cabeza y Cuello',
        'descripcion': 'Especialidad quirúrgica enfocada en intervenciones en la región de la cabeza y el cuello.',
        'acceso_directo': False
    },
    {
        'nombre': 'Cirugía de Tórax',
        'descripcion': 'Especialidad quirúrgica enfocada en intervenciones en la región torácica.',
        'acceso_directo': False
    },
    {
        'nombre': 'Cirugía Digestiva',
        'descripcion': 'Especialidad quirúrgica enfocada en intervenciones en el sistema digestivo.',
        'acceso_directo': False
    },
    {
        'nombre': 'Cirugía Proctológica',
        'descripcion': 'Especialidad quirúrgica enfocada en intervenciones en el recto y ano.',
        'acceso_directo': False
    },
    {
        'nombre': 'Medicina Física y Rehabilitación',
        'descripcion': 'Especialidad médica que se ocupa de la recuperación funcional de pacientes con discapacidades.',
        'acceso_directo': False
    }
]

# Contador para especialidades creadas y actualizadas
creadas = 0
actualizadas = 0

# Crear o actualizar especialidades
for esp_data in especialidades:
    # Intentar obtener la especialidad existente
    especialidad, created = Especialidad.objects.update_or_create(
        nombre=esp_data['nombre'],
        defaults={
            'descripcion': esp_data['descripcion'],
            'acceso_directo': esp_data['acceso_directo']
        }
    )
    
    if created:
        creadas += 1
        print(f"Creada especialidad: {especialidad.nombre}")
    else:
        actualizadas += 1
        print(f"Actualizada especialidad: {especialidad.nombre}")

print(f"\nProceso completado: {creadas} especialidades creadas, {actualizadas} actualizadas.")
print("Especialidades con acceso directo:")
for esp in Especialidad.objects.filter(acceso_directo=True):
    print(f"- {esp.nombre}")
