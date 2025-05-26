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

# Nombres y apellidos peruanos para generar médicos
nombres_hombres = [
    "Carlos", "José", "Luis", "Juan", "Pedro", "Miguel", "Jorge", "Fernando", "Ricardo", 
    "Manuel", "Víctor", "Eduardo", "Roberto", "Alberto", "César", "Mario", "Julio", 
    "Francisco", "Raúl", "Alejandro", "Héctor", "Daniel", "Oscar", "Javier", "Enrique",
    "Martín", "Guillermo", "Andrés", "Antonio", "Sergio", "Alfredo", "Ernesto", "Pablo",
    "Gustavo", "Walter", "Hugo", "Arturo", "Rubén", "Jaime", "Samuel", "Ángel", "Marco",
    "Félix", "Gerardo", "Rolando", "Augusto", "Elmer", "Teodoro", "Néstor", "Emilio"
]

nombres_mujeres = [
    "María", "Ana", "Rosa", "Luisa", "Carmen", "Silvia", "Patricia", "Laura", "Teresa", 
    "Julia", "Susana", "Martha", "Elena", "Claudia", "Pilar", "Lucía", "Beatriz", 
    "Margarita", "Cecilia", "Rosario", "Juana", "Irene", "Adriana", "Gabriela", "Mónica",
    "Sonia", "Gladys", "Roxana", "Mariela", "Flor", "Milagros", "Vilma", "Luz", "Dora",
    "Bertha", "Norma", "Yolanda", "Alicia", "Olga", "Cristina", "Liliana", "Verónica",
    "Maribel", "Esther", "Giovanna", "Edith", "Karina", "Marlene", "Nelly", "Rocío"
]

apellidos_peruanos = [
    "García", "Rodríguez", "Martínez", "López", "Pérez", "González", "Sánchez", "Ramírez", 
    "Torres", "Flores", "Rivera", "Gómez", "Díaz", "Reyes", "Morales", "Ortiz", "Cruz", 
    "Herrera", "Ramos", "Romero", "Álvarez", "Mendoza", "Vásquez", "Castillo", "Vargas",
    "Jiménez", "Cabrera", "Campos", "Fernández", "Gutiérrez", "Ríos", "Rojas", "Vega", 
    "Huamán", "Chávez", "Espinoza", "Medina", "Quispe", "Mamani", "Condori", "Huayta", 
    "Ccori", "Tapia", "Ponce", "Ayala", "Arce", "Córdova", "Miranda", "Pacheco", "Neyra",
    "Palomino", "Aguilar", "Cárdenas", "Paredes", "Salazar", "Velásquez", "Benites", 
    "Cueva", "Acosta", "Quiroz", "Melgarejo", "Valdivia", "Chacón", "Calderón", "Navarro"
]

# Función para generar un DNI único
def generar_dni_unico():
    while True:
        # Generar un DNI de 8 dígitos
        dni = ''.join(random.choices('0123456789', k=8))
        # Verificar si ya existe
        if not Usuario.objects.filter(dni=dni).exists():
            return dni

# Función para generar un CMP único
def generar_cmp_unico():
    while True:
        # Generar un CMP con formato CMP-XXXXX
        cmp = f"CMP-{random.randint(10000, 99999)}"
        # Verificar si ya existe
        if not Medico.objects.filter(cmp=cmp).exists():
            return cmp

# Función para generar un correo electrónico basado en el nombre y apellido
def generar_email(nombres, apellidos):
    # Tomar la primera letra del nombre y el primer apellido completo
    inicial = nombres.lower()[0]
    apellido = apellidos.split()[0].lower()
    # Añadir un número aleatorio para evitar duplicados
    numero = random.randint(1, 999)
    return f"{inicial}.{apellido}{numero}@hospitaltingomaria.gob.pe"

# Lista de especialidades con la cantidad de médicos a crear
especialidades_medicos = [
    {"especialidad": "Neonatología", "cantidad": 2},
    {"especialidad": "Ginecología", "cantidad": 3},
    {"especialidad": "Obstetricia", "cantidad": 5},
    {"especialidad": "Emergencias", "cantidad": 6},
    {"especialidad": "Cuidados Críticos", "cantidad": 2},
    {"especialidad": "Anestesiología", "cantidad": 3},
    {"especialidad": "Patología Clínica", "cantidad": 2},
    {"especialidad": "Anatomía Patológica", "cantidad": 1},
    {"especialidad": "Diagnóstico por Imágenes", "cantidad": 2},
    {"especialidad": "Nutrición", "cantidad": 1},
    {"especialidad": "Psicología", "cantidad": 2},
    {"especialidad": "Servicio Social", "cantidad": 2},
    {"especialidad": "Farmacia", "cantidad": 1},
    {"especialidad": "Rehabilitación", "cantidad": 1},
    {"especialidad": "Medicina General", "cantidad": 10},
    {"especialidad": "Cardiología", "cantidad": 1},
    {"especialidad": "Neumología", "cantidad": 1},
    {"especialidad": "Gastroenterología", "cantidad": 1},
    {"especialidad": "Dermatología", "cantidad": 1},
    {"especialidad": "Reumatología", "cantidad": 1},
    {"especialidad": "Cirugía General", "cantidad": 3},
    {"especialidad": "Cirugía de Cabeza y Cuello", "cantidad": 1},
    {"especialidad": "Cirugía de Tórax", "cantidad": 1},
    {"especialidad": "Cirugía Digestiva", "cantidad": 1},
    {"especialidad": "Cirugía Proctológica", "cantidad": 1},
    {"especialidad": "Medicina Física y Rehabilitación", "cantidad": 1}
]

# Contador para médicos creados
creados = 0
actualizados = 0
errores = 0

# Crear o actualizar médicos para cada especialidad
for esp_data in especialidades_medicos:
    nombre_especialidad = esp_data["especialidad"]
    cantidad = esp_data["cantidad"]
    
    try:
        # Buscar la especialidad
        try:
            especialidad = Especialidad.objects.get(nombre=nombre_especialidad)
        except Especialidad.DoesNotExist:
            print(f"Error: Especialidad '{nombre_especialidad}' no encontrada. Saltando.")
            errores += 1
            continue
        
        print(f"\nCreando {cantidad} médicos para la especialidad: {nombre_especialidad}")
        
        # Crear la cantidad especificada de médicos para esta especialidad
        for i in range(cantidad):
            # Determinar si es hombre o mujer (50% probabilidad)
            es_hombre = random.choice([True, False])
            
            if es_hombre:
                nombres = random.choice(nombres_hombres)
                genero = 'M'
            else:
                nombres = random.choice(nombres_mujeres)
                genero = 'F'
                
            apellidos = f"{random.choice(apellidos_peruanos)} {random.choice(apellidos_peruanos)}"
            dni = generar_dni_unico()
            email = generar_email(nombres, apellidos)
            cmp = generar_cmp_unico()
            
            # Crear o actualizar usuario
            usuario, created_user = Usuario.objects.update_or_create(
                dni=dni,
                defaults={
                    'username': dni,
                    'nombres': nombres,
                    'apellidos': apellidos,
                    'email': email,
                    'password': make_password('Onepiece-2000'),  # Contraseña especificada
                    'rol': rol_medico,
                    'genero': genero
                }
            )
            
            # Crear o actualizar médico
            medico, created_medico = Medico.objects.update_or_create(
                usuario=usuario,
                defaults={
                    'cmp': cmp,
                    'especialidad': especialidad
                }
            )
            
            if created_user or created_medico:
                creados += 1
                print(f"  - Creado médico: Dr. {usuario.nombres} {usuario.apellidos} - {especialidad.nombre} (DNI: {dni}, CMP: {cmp})")
            else:
                actualizados += 1
                print(f"  - Actualizado médico: Dr. {usuario.nombres} {usuario.apellidos} - {especialidad.nombre} (DNI: {dni}, CMP: {cmp})")
                
    except Exception as e:
        errores += 1
        print(f"Error al crear médicos para la especialidad {nombre_especialidad}: {str(e)}")

print(f"\nProceso completado: {creados} médicos creados, {actualizados} actualizados, {errores} errores.")
print("Todos los médicos tienen la contraseña: Onepiece-2000")
