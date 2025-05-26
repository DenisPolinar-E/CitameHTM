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

# Lista de médicos a crear para cada especialidad
medicos_por_especialidad = [
    # Neonatología - 2 médicos
    {"especialidad": "Neonatología", "nombres": "Carlos", "apellidos": "Mendoza Vargas", "dni": "10456789", "cmp": "CMP-45678", "sexo": "M"},
    {"especialidad": "Neonatología", "nombres": "María", "apellidos": "Torres Ríos", "dni": "10456790", "cmp": "CMP-45679", "sexo": "F"},
    
    # Ginecología - 3 médicos
    {"especialidad": "Ginecología", "nombres": "Laura", "apellidos": "Sánchez Torres", "dni": "10456791", "cmp": "CMP-45680", "sexo": "F"},
    {"especialidad": "Ginecología", "nombres": "Patricia", "apellidos": "Flores Castro", "dni": "10456792", "cmp": "CMP-45681", "sexo": "F"},
    {"especialidad": "Ginecología", "nombres": "Rosa", "apellidos": "Gutiérrez Paz", "dni": "10456793", "cmp": "CMP-45682", "sexo": "F"},
    
    # Obstetricia - 5 obstetras
    {"especialidad": "Obstetricia", "nombres": "Silvia", "apellidos": "Díaz Mendoza", "dni": "10456794", "cmp": "CMP-45683", "sexo": "F"},
    {"especialidad": "Obstetricia", "nombres": "Carmen", "apellidos": "Ortega Ramírez", "dni": "10456795", "cmp": "CMP-45684", "sexo": "F"},
    {"especialidad": "Obstetricia", "nombres": "Julia", "apellidos": "Ramos Castillo", "dni": "10456796", "cmp": "CMP-45685", "sexo": "F"},
    {"especialidad": "Obstetricia", "nombres": "Teresa", "apellidos": "Morales Vega", "dni": "10456797", "cmp": "CMP-45686", "sexo": "F"},
    {"especialidad": "Obstetricia", "nombres": "Lucía", "apellidos": "Fuentes Silva", "dni": "10456798", "cmp": "CMP-45687", "sexo": "F"},
    
    # Emergencias - 6 médicos
    {"especialidad": "Emergencias", "nombres": "Roberto", "apellidos": "Rojas Medina", "dni": "10456799", "cmp": "CMP-45688", "sexo": "M"},
    {"especialidad": "Emergencias", "nombres": "Miguel", "apellidos": "Vargas Campos", "dni": "10456800", "cmp": "CMP-45689", "sexo": "M"},
    {"especialidad": "Emergencias", "nombres": "Ana", "apellidos": "Herrera Soto", "dni": "10456801", "cmp": "CMP-45690", "sexo": "F"},
    {"especialidad": "Emergencias", "nombres": "Jorge", "apellidos": "Castillo Vega", "dni": "10456802", "cmp": "CMP-45691", "sexo": "M"},
    {"especialidad": "Emergencias", "nombres": "Fernando", "apellidos": "Ríos Mendoza", "dni": "10456803", "cmp": "CMP-45692", "sexo": "M"},
    {"especialidad": "Emergencias", "nombres": "Elena", "apellidos": "Medina Ortega", "dni": "10456804", "cmp": "CMP-45693", "sexo": "F"},
    
    # Cuidados Críticos - 2 médicos
    {"especialidad": "Cuidados Críticos", "nombres": "Raúl", "apellidos": "Castro Díaz", "dni": "10456805", "cmp": "CMP-45694", "sexo": "M"},
    {"especialidad": "Cuidados Críticos", "nombres": "Gabriela", "apellidos": "Soto Ramos", "dni": "10456806", "cmp": "CMP-45695", "sexo": "F"},
    
    # Anestesiología - 3 médicos
    {"especialidad": "Anestesiología", "nombres": "Héctor", "apellidos": "Vega Fuentes", "dni": "10456807", "cmp": "CMP-45696", "sexo": "M"},
    {"especialidad": "Anestesiología", "nombres": "Mónica", "apellidos": "Paredes Ruiz", "dni": "10456808", "cmp": "CMP-45697", "sexo": "F"},
    {"especialidad": "Anestesiología", "nombres": "Daniel", "apellidos": "Flores Rivera", "dni": "10456809", "cmp": "CMP-45698", "sexo": "M"},
    
    # Patología Clínica - 2 médicos
    {"especialidad": "Patología Clínica", "nombres": "Lucía", "apellidos": "Gómez López", "dni": "10456810", "cmp": "CMP-45699", "sexo": "F"},
    {"especialidad": "Patología Clínica", "nombres": "Ricardo", "apellidos": "Pérez González", "dni": "10456811", "cmp": "CMP-45700", "sexo": "M"},
    
    # Anatomía Patológica - 1 médico
    {"especialidad": "Anatomía Patológica", "nombres": "Javier", "apellidos": "Ramírez Torres", "dni": "10456812", "cmp": "CMP-45701", "sexo": "M"},
    
    # Diagnóstico por Imágenes - 2 médicos
    {"especialidad": "Diagnóstico por Imágenes", "nombres": "Silvia", "apellidos": "Cruz Herrera", "dni": "10456813", "cmp": "CMP-45702", "sexo": "F"},
    {"especialidad": "Diagnóstico por Imágenes", "nombres": "Alberto", "apellidos": "Ramos Romero", "dni": "10456814", "cmp": "CMP-45703", "sexo": "M"},
    
    # Nutrición - 1 nutricionista
    {"especialidad": "Nutrición", "nombres": "Carmen", "apellidos": "Álvarez Mendoza", "dni": "10456815", "cmp": "CMP-45704", "sexo": "F"},
    
    # Psicología - 2 psicólogos
    {"especialidad": "Psicología", "nombres": "Mario", "apellidos": "Vásquez Castillo", "dni": "10456816", "cmp": "CMP-45705", "sexo": "M"},
    {"especialidad": "Psicología", "nombres": "Laura", "apellidos": "Vargas Jiménez", "dni": "10456817", "cmp": "CMP-45706", "sexo": "F"},
    
    # Servicio Social - 2 asistentes sociales
    {"especialidad": "Servicio Social", "nombres": "Julio", "apellidos": "Cabrera Campos", "dni": "10456818", "cmp": "CMP-45707", "sexo": "M"},
    {"especialidad": "Servicio Social", "nombres": "Beatriz", "apellidos": "Fernández Gutiérrez", "dni": "10456819", "cmp": "CMP-45708", "sexo": "F"},
    
    # Farmacia - 1 farmacéutico
    {"especialidad": "Farmacia", "nombres": "Francisco", "apellidos": "Ríos Rojas", "dni": "10456820", "cmp": "CMP-45709", "sexo": "M"},
    
    # Rehabilitación - 1 médico rehabilitador
    {"especialidad": "Rehabilitación", "nombres": "Margarita", "apellidos": "Vega Huamán", "dni": "10456821", "cmp": "CMP-45710", "sexo": "F"},
    
    # Medicina General - 10 médicos
    {"especialidad": "Medicina General", "nombres": "José", "apellidos": "Chávez Espinoza", "dni": "10456822", "cmp": "CMP-45711", "sexo": "M"},
    {"especialidad": "Medicina General", "nombres": "Luis", "apellidos": "Medina Quispe", "dni": "10456823", "cmp": "CMP-45712", "sexo": "M"},
    {"especialidad": "Medicina General", "nombres": "Juan", "apellidos": "Mamani Condori", "dni": "10456824", "cmp": "CMP-45713", "sexo": "M"},
    {"especialidad": "Medicina General", "nombres": "Pedro", "apellidos": "Huayta Ccori", "dni": "10456825", "cmp": "CMP-45714", "sexo": "M"},
    {"especialidad": "Medicina General", "nombres": "María", "apellidos": "Tapia Ponce", "dni": "10456826", "cmp": "CMP-45715", "sexo": "F"},
    {"especialidad": "Medicina General", "nombres": "Ana", "apellidos": "Ayala Arce", "dni": "10456827", "cmp": "CMP-45716", "sexo": "F"},
    {"especialidad": "Medicina General", "nombres": "Rosa", "apellidos": "Córdova Miranda", "dni": "10456828", "cmp": "CMP-45717", "sexo": "F"},
    {"especialidad": "Medicina General", "nombres": "Luisa", "apellidos": "Pacheco Neyra", "dni": "10456829", "cmp": "CMP-45718", "sexo": "F"},
    {"especialidad": "Medicina General", "nombres": "Carlos", "apellidos": "Palomino Aguilar", "dni": "10456830", "cmp": "CMP-45719", "sexo": "M"},
    {"especialidad": "Medicina General", "nombres": "Víctor", "apellidos": "Cárdenas Paredes", "dni": "10456831", "cmp": "CMP-45720", "sexo": "M"},
    
    # Cardiología - 1 médico
    {"especialidad": "Cardiología", "nombres": "Eduardo", "apellidos": "Salazar Velásquez", "dni": "10456832", "cmp": "CMP-45721", "sexo": "M"},
    
    # Neumología - 1 médico
    {"especialidad": "Neumología", "nombres": "Roberto", "apellidos": "Benites Cueva", "dni": "10456833", "cmp": "CMP-45722", "sexo": "M"},
    
    # Gastroenterología - 1 médico
    {"especialidad": "Gastroenterología", "nombres": "Alberto", "apellidos": "Acosta Quiroz", "dni": "10456834", "cmp": "CMP-45723", "sexo": "M"},
    
    # Dermatología - 1 médico
    {"especialidad": "Dermatología", "nombres": "César", "apellidos": "Melgarejo Valdivia", "dni": "10456835", "cmp": "CMP-45724", "sexo": "M"},
    
    # Reumatología - 1 médico
    {"especialidad": "Reumatología", "nombres": "Mario", "apellidos": "Chacón Calderón", "dni": "10456836", "cmp": "CMP-45725", "sexo": "M"},
    
    # Cirugía General - 3 médicos
    {"especialidad": "Cirugía General", "nombres": "Julio", "apellidos": "Navarro García", "dni": "10456837", "cmp": "CMP-45726", "sexo": "M"},
    {"especialidad": "Cirugía General", "nombres": "Francisco", "apellidos": "Rodríguez Martínez", "dni": "10456838", "cmp": "CMP-45727", "sexo": "M"},
    {"especialidad": "Cirugía General", "nombres": "Raúl", "apellidos": "López Pérez", "dni": "10456839", "cmp": "CMP-45728", "sexo": "M"},
    
    # Cirugía de Cabeza y Cuello - 1 médico
    {"especialidad": "Cirugía de Cabeza y Cuello", "nombres": "Alejandro", "apellidos": "González Sánchez", "dni": "10456840", "cmp": "CMP-45729", "sexo": "M"},
    
    # Cirugía de Tórax - 1 médico
    {"especialidad": "Cirugía de Tórax", "nombres": "Héctor", "apellidos": "Ramírez Torres", "dni": "10456841", "cmp": "CMP-45730", "sexo": "M"},
    
    # Cirugía Digestiva - 1 médico
    {"especialidad": "Cirugía Digestiva", "nombres": "Daniel", "apellidos": "Flores Rivera", "dni": "10456842", "cmp": "CMP-45731", "sexo": "M"},
    
    # Cirugía Proctológica - 1 médico
    {"especialidad": "Cirugía Proctológica", "nombres": "Oscar", "apellidos": "Pérez González", "dni": "10456843", "cmp": "CMP-45732", "sexo": "M"},
    
    # Médico Rehabilitador - 1 médico
    {"especialidad": "Medicina Física y Rehabilitación", "nombres": "Javier", "apellidos": "Ramírez Torres", "dni": "10456844", "cmp": "CMP-45733", "sexo": "M"}
]

# Contador para médicos creados
creados = 0
actualizados = 0
errores = 0

# Crear o actualizar médicos
for medico_data in medicos_por_especialidad:
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
                'sexo': medico_data['sexo']
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
