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

# Especialidades faltantes con la cantidad de médicos a crear
especialidades_faltantes = {
    "Cardiología": 1,
    "Cirugía Digestiva": 1,
    "Cirugía General": 3,
    "Cirugía Proctológica": 1,
    "Cirugía de Cabeza y Cuello": 1,
    "Cirugía de Tórax": 1,
    "Dermatología": 1,
    "Farmacia": 1,
    "Gastroenterología": 1,
    "Medicina Física y Rehabilitación": 1,
    "Medicina General": 9,
    "Neumología": 1,
    "Rehabilitación": 1,
    "Reumatología": 1,
    "Servicio Social": 2
}

# Nombres y apellidos para generar médicos
nombres_hombres = [
    "Carlos", "José", "Luis", "Juan", "Pedro", "Miguel", "Jorge", "Fernando", "Ricardo", 
    "Manuel", "Víctor", "Eduardo", "Roberto", "Alberto", "César", "Mario", "Julio", 
    "Francisco", "Raúl", "Alejandro", "Héctor", "Daniel", "Oscar", "Javier", "Enrique"
]

nombres_mujeres = [
    "María", "Ana", "Rosa", "Luisa", "Carmen", "Silvia", "Patricia", "Laura", "Teresa", 
    "Julia", "Susana", "Martha", "Elena", "Claudia", "Pilar", "Lucía", "Beatriz", 
    "Margarita", "Cecilia", "Rosario", "Juana", "Irene", "Adriana", "Gabriela", "Mónica"
]

apellidos_peruanos = [
    "García", "Rodríguez", "Martínez", "López", "Pérez", "González", "Sánchez", "Ramírez", 
    "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Reyes", "Morales", "Ortiz", "Cruz", 
    "Herrera", "Ramos", "Romero", "Álvarez", "Mendoza", "Vásquez", "Castillo", "Vargas"
]

# Función para generar un DNI único basado en la especialidad y el índice
def generar_dni(especialidad_id, indice):
    # Formato: 3EEIII (3 + ID especialidad de 2 dígitos + índice de 3 dígitos)
    return f"3{especialidad_id:02d}{indice:03d}"

# Función para generar un CMP único
def generar_cmp(especialidad_id, indice):
    # Formato: CMP-EEIII (CMP- + ID especialidad de 2 dígitos + índice de 3 dígitos)
    return f"CMP-{especialidad_id:02d}{indice:03d}"

# Contador para médicos creados
total_creados = 0
total_errores = 0

# Crear médicos faltantes para cada especialidad
for nombre_especialidad, cantidad in especialidades_faltantes.items():
    try:
        # Buscar la especialidad
        try:
            especialidad = Especialidad.objects.get(nombre=nombre_especialidad)
            print(f"\nProcesando especialidad: {nombre_especialidad} (ID: {especialidad.id})")
        except Especialidad.DoesNotExist:
            print(f"Error: Especialidad '{nombre_especialidad}' no encontrada. Saltando.")
            continue
        
        # Contar médicos existentes
        medicos_existentes = Medico.objects.filter(especialidad=especialidad).count()
        print(f"  Médicos existentes: {medicos_existentes}, A crear: {cantidad}")
        
        # Crear médicos faltantes en una transacción
        with transaction.atomic():
            creados_especialidad = 0
            
            for i in range(1, cantidad + 1):
                try:
                    # Determinar si es hombre o mujer (alternar)
                    es_hombre = (i % 2 == 0)
                    
                    if es_hombre:
                        nombres = nombres_hombres[(especialidad.id + i) % len(nombres_hombres)]
                        sexo = 'M'
                    else:
                        nombres = nombres_mujeres[(especialidad.id + i) % len(nombres_mujeres)]
                        sexo = 'F'
                    
                    # Generar apellidos únicos
                    apellido1 = apellidos_peruanos[(especialidad.id + i) % len(apellidos_peruanos)]
                    apellido2 = apellidos_peruanos[(especialidad.id + i + 5) % len(apellidos_peruanos)]
                    apellidos = f"{apellido1} {apellido2}"
                    
                    # Generar DNI y CMP únicos
                    indice = medicos_existentes + i
                    dni = generar_dni(especialidad.id, indice)
                    cmp = generar_cmp(especialidad.id, indice)
                    
                    # Generar email
                    email = f"{nombres.lower()[0]}.{apellido1.lower()}{indice}@hospitaltingomaria.gob.pe"
                    
                    # Crear usuario
                    usuario = Usuario.objects.create(
                        username=dni,
                        nombres=nombres,
                        apellidos=apellidos,
                        dni=dni,
                        email=email,
                        password=make_password('Onepiece-2000'),
                        rol=rol_medico,
                        sexo=sexo
                    )
                    
                    # Crear médico
                    Medico.objects.create(
                        usuario=usuario,
                        cmp=cmp,
                        especialidad=especialidad
                    )
                    
                    creados_especialidad += 1
                    print(f"    Creado médico {i}/{cantidad}: Dr. {nombres} {apellidos} (DNI: {dni}, CMP: {cmp})")
                    
                except Exception as e:
                    print(f"    Error al crear médico {i}/{cantidad}: {str(e)}")
                    total_errores += 1
            
            total_creados += creados_especialidad
            print(f"  Completado: {creados_especialidad} médicos creados para {nombre_especialidad}")
            
    except Exception as e:
        print(f"Error general procesando especialidad {nombre_especialidad}: {str(e)}")
        total_errores += 1

print(f"\nProceso completado: {total_creados} médicos creados, {total_errores} errores.")
print("Todos los médicos tienen la contraseña: Onepiece-2000")
