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

# Definir la cantidad de médicos por especialidad
especialidades_cantidad = {
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

# Contador para médicos creados
total_creados = 0
total_errores = 0

# Función para generar un DNI único
def generar_dni_base(indice, especialidad_id):
    # Usar el índice y el ID de especialidad para generar un DNI único
    # Formato: 1EEII (1 + ID especialidad de 2 dígitos + índice de 2 dígitos)
    return f"1{especialidad_id:02d}{indice:02d}"

# Función para generar un CMP único
def generar_cmp(indice, especialidad_id):
    # Usar el índice y el ID de especialidad para generar un CMP único
    return f"CMP-{especialidad_id}{indice:02d}"

# Procesar cada especialidad
for nombre_especialidad, cantidad in especialidades_cantidad.items():
    try:
        # Buscar la especialidad
        try:
            especialidad = Especialidad.objects.get(nombre=nombre_especialidad)
            print(f"\nProcesando especialidad: {nombre_especialidad} (ID: {especialidad.id}) - {cantidad} médicos")
        except Especialidad.DoesNotExist:
            print(f"Error: Especialidad '{nombre_especialidad}' no encontrada. Saltando.")
            continue
        
        # Crear médicos para esta especialidad en una sola transacción
        with transaction.atomic():
            creados_especialidad = 0
            errores_especialidad = 0
            
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
                    dni_base = generar_dni_base(i, especialidad.id)
                    # Añadir dígitos aleatorios para completar 8 dígitos
                    dni = f"{dni_base}{'0' * (8 - len(dni_base))}"
                    cmp = generar_cmp(i, especialidad.id)
                    
                    # Generar email
                    email = f"{nombres.lower()[0]}.{apellido1.lower()}@hospitaltingomaria.gob.pe"
                    
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
                    print(f"  Creado médico {i}/{cantidad}: Dr. {nombres} {apellidos} (DNI: {dni}, CMP: {cmp})")
                    
                except Exception as e:
                    errores_especialidad += 1
                    print(f"  Error al crear médico {i}/{cantidad}: {str(e)}")
            
            total_creados += creados_especialidad
            total_errores += errores_especialidad
            print(f"Completado: {creados_especialidad} médicos creados, {errores_especialidad} errores para {nombre_especialidad}")
            
    except Exception as e:
        print(f"Error general procesando especialidad {nombre_especialidad}: {str(e)}")

print(f"\nProceso completado: {total_creados} médicos creados, {total_errores} errores.")
print("Todos los médicos tienen la contraseña: Onepiece-2000")
