import os
import django
import random
from django.db import transaction

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Usuario, Medico, Especialidad

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

# Contador para médicos eliminados
total_eliminados = 0

# Procesar cada especialidad
for nombre_especialidad, cantidad_requerida in especialidades_requeridas.items():
    try:
        # Buscar la especialidad
        try:
            especialidad = Especialidad.objects.get(nombre=nombre_especialidad)
            print(f"\nProcesando especialidad: {nombre_especialidad}")
        except Especialidad.DoesNotExist:
            print(f"Error: Especialidad '{nombre_especialidad}' no encontrada. Saltando.")
            continue
        
        # Obtener todos los médicos de esta especialidad
        medicos = list(Medico.objects.filter(especialidad=especialidad))
        cantidad_actual = len(medicos)
        
        if cantidad_actual <= cantidad_requerida:
            print(f"  No es necesario eliminar médicos. Actuales: {cantidad_actual}, Requeridos: {cantidad_requerida}")
            continue
        
        # Calcular cuántos médicos eliminar
        a_eliminar = cantidad_actual - cantidad_requerida
        print(f"  Médicos actuales: {cantidad_actual}, Requeridos: {cantidad_requerida}, A eliminar: {a_eliminar}")
        
        # Seleccionar médicos a eliminar al azar
        medicos_a_eliminar = random.sample(medicos, a_eliminar)
        
        # Eliminar médicos seleccionados en una transacción
        with transaction.atomic():
            eliminados_especialidad = 0
            
            for medico in medicos_a_eliminar:
                try:
                    usuario = medico.usuario
                    nombre_completo = f"Dr. {usuario.nombres} {usuario.apellidos}"
                    dni = usuario.dni
                    cmp = medico.cmp
                    
                    # Eliminar médico y usuario
                    medico.delete()
                    usuario.delete()
                    
                    eliminados_especialidad += 1
                    print(f"    Eliminado médico: {nombre_completo} (DNI: {dni}, CMP: {cmp})")
                    
                except Exception as e:
                    print(f"    Error al eliminar médico: {str(e)}")
            
            total_eliminados += eliminados_especialidad
            print(f"  Completado: {eliminados_especialidad} médicos eliminados para {nombre_especialidad}")
            
    except Exception as e:
        print(f"Error general procesando especialidad {nombre_especialidad}: {str(e)}")

# Eliminar la especialidad "General" si existe
try:
    especialidad_general = Especialidad.objects.get(nombre="General")
    medicos_general = Medico.objects.filter(especialidad=especialidad_general)
    
    if medicos_general.exists():
        print("\nEliminando médicos de la especialidad 'General' (no requerida)")
        
        with transaction.atomic():
            for medico in medicos_general:
                usuario = medico.usuario
                nombre_completo = f"Dr. {usuario.nombres} {usuario.apellidos}"
                dni = usuario.dni
                cmp = medico.cmp
                
                medico.delete()
                usuario.delete()
                
                total_eliminados += 1
                print(f"  Eliminado médico: {nombre_completo} (DNI: {dni}, CMP: {cmp})")
except Especialidad.DoesNotExist:
    print("\nLa especialidad 'General' no existe, no es necesario eliminar médicos.")
except Exception as e:
    print(f"\nError al eliminar médicos de la especialidad 'General': {str(e)}")

print(f"\nProceso completado: {total_eliminados} médicos eliminados en total.")
