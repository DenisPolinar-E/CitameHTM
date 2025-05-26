import os
import django
import random
from datetime import datetime, timedelta, time

# Configurar el entorno de Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Medico, DisponibilidadMedica

# Constantes para los turnos
DIAS_SEMANA = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo'
}

TURNOS = {
    'mañana': {
        'inicio': time(8, 0),
        'fin': time(14, 0)
    },
    'tarde': {
        'inicio': time(14, 0),
        'fin': time(20, 0)
    },
    'noche': {
        'inicio': time(20, 0),
        'fin': time(8, 0)  # Para guardias nocturnas
    }
}

# Obtener todos los médicos
medicos = Medico.objects.all()
if not medicos:
    print("No hay médicos registrados en el sistema.")
    exit()

# Contador para disponibilidades creadas
creadas = 0
actualizadas = 0
errores = 0

# Eliminar disponibilidades existentes (opcional, comentar si no se desea eliminar)
# DisponibilidadMedica.objects.all().delete()
# print("Disponibilidades existentes eliminadas.")

print(f"Creando disponibilidades para {medicos.count()} médicos...")

# Crear disponibilidades para cada médico
for medico in medicos:
    try:
        print(f"\nConfigurando horarios para: Dr. {medico.usuario.nombres} {medico.usuario.apellidos} - {medico.especialidad.nombre}")
        
        # Determinar cuántos días a la semana trabaja este médico (entre 3 y 6 días)
        dias_trabajo = random.randint(3, 6)
        
        # Seleccionar días aleatorios de la semana (excluyendo domingo para la mayoría)
        dias_seleccionados = random.sample(range(0, 6), dias_trabajo)
        
        # Algunos médicos trabajan domingos (guardias)
        if random.random() < 0.2:  # 20% de probabilidad de trabajar domingo
            if 6 not in dias_seleccionados:
                dias_seleccionados.append(6)
        
        # Para cada día, asignar un turno
        for dia in dias_seleccionados:
            # Determinar el tipo de turno para este día
            tipo_turno = random.choice(['mañana', 'tarde', 'noche'] if dia == 6 else ['mañana', 'tarde'])
            
            # Crear disponibilidad regular
            disponibilidad, created = DisponibilidadMedica.objects.update_or_create(
                medico=medico,
                dia_semana=dia,
                hora_inicio=TURNOS[tipo_turno]['inicio'],
                defaults={
                    'hora_fin': TURNOS[tipo_turno]['fin'],
                    'tipo_turno': tipo_turno,
                    'activo': True
                }
            )
            
            if created:
                creadas += 1
                print(f"  - Creado turno regular: {DIAS_SEMANA[dia]}, {tipo_turno} ({TURNOS[tipo_turno]['inicio']} - {TURNOS[tipo_turno]['fin']})")
            else:
                actualizadas += 1
                print(f"  - Actualizado turno regular: {DIAS_SEMANA[dia]}, {tipo_turno} ({TURNOS[tipo_turno]['inicio']} - {TURNOS[tipo_turno]['fin']})")
        
        # Crear algunas disponibilidades especiales (fechas específicas)
        # Por ejemplo, guardias extra o reemplazos
        num_fechas_especiales = random.randint(0, 3)  # Entre 0 y 3 fechas especiales
        
        for _ in range(num_fechas_especiales):
            # Fecha aleatoria en los próximos 30 días
            dias_adelante = random.randint(1, 30)
            fecha_especial = (datetime.now() + timedelta(days=dias_adelante)).date()
            
            # Tipo de turno para esta fecha especial
            tipo_turno_especial = random.choice(['mañana', 'tarde', 'noche'])
            
            # Crear disponibilidad especial
            disponibilidad_esp, created_esp = DisponibilidadMedica.objects.update_or_create(
                medico=medico,
                fecha_especial=fecha_especial,
                defaults={
                    'hora_inicio': TURNOS[tipo_turno_especial]['inicio'],
                    'hora_fin': TURNOS[tipo_turno_especial]['fin'],
                    'tipo_turno': tipo_turno_especial,
                    'activo': True
                }
            )
            
            if created_esp:
                creadas += 1
                print(f"  - Creado turno especial: {fecha_especial.strftime('%d/%m/%Y')}, {tipo_turno_especial}")
            else:
                actualizadas += 1
                print(f"  - Actualizado turno especial: {fecha_especial.strftime('%d/%m/%Y')}, {tipo_turno_especial}")
        
        # Crear algunas disponibilidades inactivas (vacaciones, licencias, etc.)
        if random.random() < 0.3:  # 30% de probabilidad de tener días inactivos
            num_inactivos = random.randint(1, 5)  # Entre 1 y 5 días inactivos
            
            for _ in range(num_inactivos):
                # Fecha aleatoria en los próximos 60 días
                dias_adelante = random.randint(15, 60)
                fecha_inactiva = (datetime.now() + timedelta(days=dias_adelante)).date()
                
                # Tipo de turno que estaría inactivo
                tipo_turno_inactivo = random.choice(['mañana', 'tarde', 'noche'])
                
                # Crear disponibilidad inactiva
                disponibilidad_inactiva, created_inactiva = DisponibilidadMedica.objects.update_or_create(
                    medico=medico,
                    fecha_especial=fecha_inactiva,
                    defaults={
                        'hora_inicio': TURNOS[tipo_turno_inactivo]['inicio'],
                        'hora_fin': TURNOS[tipo_turno_inactivo]['fin'],
                        'tipo_turno': tipo_turno_inactivo,
                        'activo': False  # Marcado como inactivo
                    }
                )
                
                if created_inactiva:
                    creadas += 1
                    print(f"  - Creado día inactivo: {fecha_inactiva.strftime('%d/%m/%Y')} (vacaciones/licencia)")
                else:
                    actualizadas += 1
                    print(f"  - Actualizado día inactivo: {fecha_inactiva.strftime('%d/%m/%Y')} (vacaciones/licencia)")
    
    except Exception as e:
        errores += 1
        print(f"Error al configurar horarios para Dr. {medico.usuario.nombres} {medico.usuario.apellidos}: {str(e)}")

print(f"\nProceso completado: {creadas} disponibilidades creadas, {actualizadas} actualizadas, {errores} errores.")
print("Los médicos ahora tienen horarios configurados que simulan un hospital público real.")
