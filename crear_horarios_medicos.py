import os
import django
import random
from datetime import time, timedelta, date, datetime
from django.db import transaction

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Medico, DisponibilidadMedica, Especialidad, Consultorio

# Crear consultorios si no existen
def crear_consultorios():
    # Verificar si ya existen consultorios
    if Consultorio.objects.exists():
        print("Ya existen consultorios en el sistema. No se crearán nuevos.")
        return
    
    # Crear consultorios por pisos y áreas
    consultorios = [
        # Piso 1 - Consulta Externa
        {"codigo": "101", "piso": "1", "area": "Consulta Externa"},
        {"codigo": "102", "piso": "1", "area": "Consulta Externa"},
        {"codigo": "103", "piso": "1", "area": "Consulta Externa"},
        {"codigo": "104", "piso": "1", "area": "Consulta Externa"},
        {"codigo": "105", "piso": "1", "area": "Consulta Externa"},
        {"codigo": "106", "piso": "1", "area": "Consulta Externa"},
        {"codigo": "107", "piso": "1", "area": "Consulta Externa"},
        {"codigo": "108", "piso": "1", "area": "Consulta Externa"},
        
        # Piso 1 - Emergencia
        {"codigo": "E01", "piso": "1", "area": "Emergencia"},
        {"codigo": "E02", "piso": "1", "area": "Emergencia"},
        {"codigo": "E03", "piso": "1", "area": "Emergencia"},
        
        # Piso 2 - Especialidades
        {"codigo": "201", "piso": "2", "area": "Especialidades"},
        {"codigo": "202", "piso": "2", "area": "Especialidades"},
        {"codigo": "203", "piso": "2", "area": "Especialidades"},
        {"codigo": "204", "piso": "2", "area": "Especialidades"},
        {"codigo": "205", "piso": "2", "area": "Especialidades"},
        
        # Piso 2 - Cirugía
        {"codigo": "C01", "piso": "2", "area": "Cirugía"},
        {"codigo": "C02", "piso": "2", "area": "Cirugía"},
        
        # Piso 3 - Ginecología y Obstetricia
        {"codigo": "301", "piso": "3", "area": "Ginecología y Obstetricia"},
        {"codigo": "302", "piso": "3", "area": "Ginecología y Obstetricia"},
        {"codigo": "303", "piso": "3", "area": "Ginecología y Obstetricia"},
        
        # Piso 3 - Pediatría
        {"codigo": "P01", "piso": "3", "area": "Pediatría"},
        {"codigo": "P02", "piso": "3", "area": "Pediatría"},
        
        # Servicios de apoyo
        {"codigo": "D01", "piso": "1", "area": "Diagnóstico por Imágenes"},
        {"codigo": "D02", "piso": "1", "area": "Diagnóstico por Imágenes"},
        {"codigo": "L01", "piso": "1", "area": "Laboratorio"},
        {"codigo": "L02", "piso": "1", "area": "Laboratorio"},
        {"codigo": "F01", "piso": "1", "area": "Farmacia"},
        {"codigo": "N01", "piso": "1", "area": "Nutrición"},
        {"codigo": "PS1", "piso": "2", "area": "Psicología"},
        {"codigo": "SS1", "piso": "2", "area": "Servicio Social"},
    ]
    
    with transaction.atomic():
        for c in consultorios:
            Consultorio.objects.create(
                codigo=c["codigo"],
                piso=c["piso"],
                area=c["area"]
            )
    
    print(f"Se crearon {len(consultorios)} consultorios.")

# Función para convertir hora en formato string a objeto time
def str_to_time(hora_str):
    hora, minuto = map(int, hora_str.split(':'))
    return time(hour=hora, minute=minuto)

# Configuración de horarios por tipo de especialidad
def configurar_horarios_por_especialidad():
    # Diccionario con configuraciones de horarios por tipo de especialidad
    return {
        "alta_demanda": {
            "especialidades": ["Medicina General", "Emergencias"],
            "turnos": [
                {"tipo": "mañana", "inicio": "07:00", "fin": "13:00"},
                {"tipo": "tarde", "inicio": "13:00", "fin": "19:00"},
                {"tipo": "noche", "inicio": "19:00", "fin": "07:00"},  # Para emergencias
            ],
            "dias_semana": [0, 1, 2, 3, 4, 5, 6],  # Todos los días para emergencias
            "dias_laborables": [0, 1, 2, 3, 4],  # Lunes a viernes para medicina general
            "distribucion": {
                "Medicina General": {
                    "mañana": 5,  # 5 médicos en turno mañana
                    "tarde": 5,   # 5 médicos en turno tarde
                },
                "Emergencias": {
                    "mañana": 2,  # 2 médicos en turno mañana
                    "tarde": 2,   # 2 médicos en turno tarde
                    "noche": 2,   # 2 médicos en turno noche
                }
            }
        },
        "quirurgicas": {
            "especialidades": ["Cirugía General", "Cirugía Digestiva", "Cirugía de Cabeza y Cuello", 
                              "Cirugía de Tórax", "Cirugía Proctológica"],
            "turnos": [
                {"tipo": "mañana", "inicio": "08:00", "fin": "14:00"},
                {"tipo": "tarde", "inicio": "14:00", "fin": "20:00"},
            ],
            "dias_semana": [0, 1, 2, 3, 4],  # Lunes a viernes
            "distribucion": {
                "Cirugía General": {
                    "mañana": 2,  # 2 cirujanos en turno mañana
                    "tarde": 1,   # 1 cirujano en turno tarde
                },
                "default": {
                    "mañana": 1,  # 1 cirujano especialista en turno mañana
                    "tarde": 0,   # Ninguno en turno tarde (solo atienden mañanas)
                }
            }
        },
        "materno_infantil": {
            "especialidades": ["Ginecología", "Obstetricia", "Neonatología"],
            "turnos": [
                {"tipo": "mañana", "inicio": "07:00", "fin": "13:00"},
                {"tipo": "tarde", "inicio": "13:00", "fin": "19:00"},
                {"tipo": "guardia", "inicio": "19:00", "fin": "07:00"},
            ],
            "dias_semana": [0, 1, 2, 3, 4, 5, 6],  # Todos los días
            "distribucion": {
                "Ginecología": {
                    "mañana": 2,
                    "tarde": 1,
                    "guardia": 0,
                },
                "Obstetricia": {
                    "mañana": 2,
                    "tarde": 2,
                    "guardia": 1,
                },
                "Neonatología": {
                    "mañana": 1,
                    "tarde": 1,
                    "guardia": 0,
                }
            }
        },
        "diagnostico": {
            "especialidades": ["Diagnóstico por Imágenes", "Patología Clínica", "Anatomía Patológica"],
            "turnos": [
                {"tipo": "mañana", "inicio": "07:00", "fin": "13:00"},
                {"tipo": "tarde", "inicio": "13:00", "fin": "19:00"},
            ],
            "dias_semana": [0, 1, 2, 3, 4],  # Lunes a viernes
            "distribucion": {
                "Diagnóstico por Imágenes": {
                    "mañana": 1,
                    "tarde": 1,
                },
                "Patología Clínica": {
                    "mañana": 1,
                    "tarde": 1,
                },
                "Anatomía Patológica": {
                    "mañana": 1,
                    "tarde": 0,
                }
            }
        },
        "especialidades_medicas": {
            "especialidades": ["Cardiología", "Neumología", "Gastroenterología", "Dermatología", 
                              "Reumatología", "Medicina Física y Rehabilitación", "Rehabilitación"],
            "turnos": [
                {"tipo": "mañana", "inicio": "08:00", "fin": "14:00"},
                {"tipo": "tarde", "inicio": "14:00", "fin": "20:00"},
            ],
            "dias_semana": [0, 1, 2, 3, 4],  # Lunes a viernes
            "dias_especificos": {
                "Cardiología": [0, 2, 4],       # Lunes, Miércoles, Viernes
                "Neumología": [1, 3],           # Martes, Jueves
                "Gastroenterología": [0, 3],    # Lunes, Jueves
                "Dermatología": [1, 4],         # Martes, Viernes
                "Reumatología": [2],            # Miércoles
                "Medicina Física y Rehabilitación": [0, 2, 4],  # Lunes, Miércoles, Viernes
                "Rehabilitación": [1, 3]        # Martes, Jueves
            },
            "distribucion": {
                "default": {
                    "mañana": 1,
                    "tarde": 0,
                }
            }
        },
        "apoyo": {
            "especialidades": ["Psicología", "Servicio Social", "Nutrición", "Farmacia", "Anestesiología", "Cuidados Críticos"],
            "turnos": [
                {"tipo": "mañana", "inicio": "07:00", "fin": "13:00"},
                {"tipo": "tarde", "inicio": "13:00", "fin": "19:00"},
                {"tipo": "guardia", "inicio": "19:00", "fin": "07:00"},
            ],
            "dias_semana": [0, 1, 2, 3, 4],  # Lunes a viernes
            "distribucion": {
                "Psicología": {
                    "mañana": 1,
                    "tarde": 1,
                },
                "Servicio Social": {
                    "mañana": 1,
                    "tarde": 1,
                },
                "Nutrición": {
                    "mañana": 1,
                    "tarde": 0,
                },
                "Farmacia": {
                    "mañana": 1,
                    "tarde": 0,
                },
                "Anestesiología": {
                    "mañana": 2,
                    "tarde": 1,
                },
                "Cuidados Críticos": {
                    "mañana": 1,
                    "tarde": 1,
                }
            }
        },
        "odontologia": {
            "especialidades": ["Odontología"],
            "turnos": [
                {"tipo": "mañana", "inicio": "08:00", "fin": "14:00"},
                {"tipo": "tarde", "inicio": "14:00", "fin": "20:00"},
            ],
            "dias_semana": [0, 1, 2, 3, 4],  # Lunes a viernes
            "distribucion": {
                "Odontología": {
                    "mañana": 2,
                    "tarde": 1,
                }
            }
        }
    }

# Función para crear disponibilidades médicas
def crear_disponibilidades():
    # Eliminar disponibilidades existentes
    DisponibilidadMedica.objects.all().delete()
    print("Disponibilidades anteriores eliminadas.")
    
    # Configuración de horarios
    config_horarios = configurar_horarios_por_especialidad()
    
    # Obtener todas las especialidades
    especialidades = Especialidad.objects.all()
    
    # Contador de disponibilidades creadas
    total_disponibilidades = 0
    
    # Procesar cada tipo de especialidad
    for tipo_esp, config in config_horarios.items():
        print(f"\nConfigurando horarios para: {tipo_esp}")
        
        # Procesar cada especialidad de este tipo
        for nombre_esp in config["especialidades"]:
            try:
                especialidad = especialidades.get(nombre=nombre_esp)
                print(f"  Especialidad: {nombre_esp}")
                
                # Obtener médicos de esta especialidad
                medicos = list(Medico.objects.filter(especialidad=especialidad))
                if not medicos:
                    print(f"    No hay médicos en la especialidad {nombre_esp}")
                    continue
                
                print(f"    {len(medicos)} médicos encontrados")
                
                # Determinar días de la semana para esta especialidad
                if nombre_esp in config.get("dias_especificos", {}):
                    dias_semana = config["dias_especificos"][nombre_esp]
                else:
                    dias_semana = config["dias_semana"]
                
                # Obtener distribución de turnos para esta especialidad
                if nombre_esp in config["distribucion"]:
                    distribucion = config["distribucion"][nombre_esp]
                else:
                    distribucion = config["distribucion"].get("default", {})
                
                # Crear disponibilidades para cada turno
                for turno in config["turnos"]:
                    tipo_turno = turno["tipo"]
                    hora_inicio = str_to_time(turno["inicio"])
                    hora_fin = str_to_time(turno["fin"])
                    
                    # Verificar si este turno aplica para esta especialidad
                    num_medicos_turno = distribucion.get(tipo_turno, 0)
                    if num_medicos_turno == 0:
                        continue
                    
                    print(f"    Turno {tipo_turno}: {num_medicos_turno} médicos")
                    
                    # Si hay más turnos que médicos, algunos médicos tendrán múltiples turnos
                    medicos_asignados = []
                    
                    # Para cada día de la semana
                    for dia in dias_semana:
                        # Seleccionar médicos para este turno y día
                        medicos_disponibles = [m for m in medicos if m not in medicos_asignados]
                        if not medicos_disponibles:
                            # Si todos los médicos ya están asignados, reiniciar la lista
                            medicos_asignados = []
                            medicos_disponibles = medicos
                        
                        # Seleccionar médicos para este turno
                        medicos_turno = random.sample(
                            medicos_disponibles, 
                            min(num_medicos_turno, len(medicos_disponibles))
                        )
                        
                        # Crear disponibilidad para cada médico seleccionado
                        for medico in medicos_turno:
                            medicos_asignados.append(medico)
                            
                            # Verificar si el médico ya tiene un turno ese día
                            tiene_turno = DisponibilidadMedica.objects.filter(
                                medico=medico,
                                dia_semana=dia
                            ).exists()
                            
                            # Solo crear disponibilidad si no tiene otro turno ese día
                            # Excepto para Emergencias que pueden tener múltiples turnos
                            if not tiene_turno or nombre_esp == "Emergencias":
                                # Crear disponibilidad
                                DisponibilidadMedica.objects.create(
                                    medico=medico,
                                    dia_semana=dia,
                                    hora_inicio=hora_inicio,
                                    hora_fin=hora_fin,
                                    tipo_turno=tipo_turno,
                                    activo=True
                                )
                                total_disponibilidades += 1
                
                # Casos especiales para emergencias y guardias
                if nombre_esp == "Emergencias":
                    # Crear un registro de médicos y sus días de guardia
                    guardias_medicos = {}
                    for medico in medicos:
                        guardias_medicos[medico.id] = []
                    
                    # Distribuir guardias de fin de semana equitativamente
                    # Asignar guardias de sábado
                    medicos_sabado = random.sample(medicos, min(3, len(medicos)))
                    for medico in medicos_sabado:
                        DisponibilidadMedica.objects.create(
                            medico=medico,
                            dia_semana=5,  # Sábado
                            hora_inicio=str_to_time("08:00"),
                            hora_fin=str_to_time("20:00"),
                            tipo_turno="guardia",
                            activo=True
                        )
                        total_disponibilidades += 1
                        guardias_medicos[medico.id].append(5)  # Registrar guardia de sábado
                    
                    # Asignar guardias de domingo a médicos diferentes
                    medicos_disponibles_domingo = [m for m in medicos if m not in medicos_sabado]
                    if not medicos_disponibles_domingo:  # Si todos los médicos ya tienen guardia el sábado
                        medicos_disponibles_domingo = medicos
                    
                    medicos_domingo = random.sample(medicos_disponibles_domingo, min(3, len(medicos_disponibles_domingo)))
                    for medico in medicos_domingo:
                        DisponibilidadMedica.objects.create(
                            medico=medico,
                            dia_semana=6,  # Domingo
                            hora_inicio=str_to_time("08:00"),
                            hora_fin=str_to_time("20:00"),
                            tipo_turno="guardia",
                            activo=True
                        )
                        total_disponibilidades += 1
                        guardias_medicos[medico.id].append(6)  # Registrar guardia de domingo
                
                # Agregar reuniones administrativas (2 horas semanales) - solo en días laborables
                if len(medicos) > 1:
                    # Filtrar solo días laborables (0-4, lunes a viernes)
                    dias_laborables = [d for d in dias_semana if d < 5]
                    if dias_laborables:
                        # Día de reunión (último día laborable de la semana para esta especialidad)
                        dia_reunion = max(dias_laborables)
                        
                        # Crear un registro de médicos que ya tienen turno ese día
                        medicos_con_turno_dia_reunion = set()
                        for disp in DisponibilidadMedica.objects.filter(dia_semana=dia_reunion):
                            medicos_con_turno_dia_reunion.add(disp.medico.id)
                        
                        for medico in medicos:
                            # Verificar si el médico ya tiene un turno ese día
                            if medico.id not in medicos_con_turno_dia_reunion:
                                DisponibilidadMedica.objects.create(
                                    medico=medico,
                                    dia_semana=dia_reunion,
                                    hora_inicio=str_to_time("15:00"),
                                    hora_fin=str_to_time("17:00"),
                                    tipo_turno="tarde",  # Usando 'tarde' en lugar de 'reunión' para cumplir con TIPO_TURNO_CHOICES
                                    activo=True
                                )
                                total_disponibilidades += 1
                                medicos_con_turno_dia_reunion.add(medico.id)
                
            except Especialidad.DoesNotExist:
                print(f"  Especialidad {nombre_esp} no encontrada")
                continue
    
    print(f"\nProceso completado: {total_disponibilidades} disponibilidades médicas creadas.")

# Función principal
def main():
    print("Iniciando creación de horarios para médicos del Hospital de Tingo María...")
    
    # Crear consultorios si no existen
    crear_consultorios()
    
    # Crear disponibilidades médicas
    crear_disponibilidades()
    
    print("\nProceso finalizado. Se han creado los horarios para todos los médicos.")
    print("Ahora los pacientes pueden reservar citas en los horarios disponibles.")

if __name__ == "__main__":
    main()
