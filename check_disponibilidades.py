import os
import django
from datetime import datetime, timedelta

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos
from core.models import Medico, DisponibilidadMedica

# Mapeo de días de la semana
DIAS_SEMANA = {
    0: 'Lunes',
    1: 'Martes',
    2: 'Miércoles',
    3: 'Jueves',
    4: 'Viernes',
    5: 'Sábado',
    6: 'Domingo'
}

# Obtener todos los médicos
medicos = Medico.objects.all()
total_disponibilidades = DisponibilidadMedica.objects.count()

print(f"=== RESUMEN DE DISPONIBILIDADES ===")
print(f"Total de médicos: {medicos.count()}")
print(f"Total de disponibilidades: {total_disponibilidades}")
print(f"Promedio de disponibilidades por médico: {total_disponibilidades / medicos.count() if medicos.count() > 0 else 0:.2f}")

# Disponibilidades regulares vs especiales
disponibilidades_regulares = DisponibilidadMedica.objects.filter(fecha_especial__isnull=True).count()
disponibilidades_especiales = DisponibilidadMedica.objects.filter(fecha_especial__isnull=False).count()
disponibilidades_activas = DisponibilidadMedica.objects.filter(activo=True).count()
disponibilidades_inactivas = DisponibilidadMedica.objects.filter(activo=False).count()

print(f"Disponibilidades regulares: {disponibilidades_regulares}")
print(f"Disponibilidades especiales: {disponibilidades_especiales}")
print(f"Disponibilidades activas: {disponibilidades_activas}")
print(f"Disponibilidades inactivas: {disponibilidades_inactivas}")

# Mostrar disponibilidades por tipo de turno
turnos_manana = DisponibilidadMedica.objects.filter(tipo_turno='mañana').count()
turnos_tarde = DisponibilidadMedica.objects.filter(tipo_turno='tarde').count()
turnos_noche = DisponibilidadMedica.objects.filter(tipo_turno='noche').count()

print(f"\nDistribución por tipo de turno:")
print(f"Turnos de mañana: {turnos_manana}")
print(f"Turnos de tarde: {turnos_tarde}")
print(f"Turnos de noche: {turnos_noche}")

# Mostrar disponibilidades por día de la semana
print(f"\nDistribución por día de la semana:")
for dia_num, dia_nombre in DIAS_SEMANA.items():
    count = DisponibilidadMedica.objects.filter(dia_semana=dia_num).count()
    print(f"{dia_nombre}: {count} disponibilidades")

# Mostrar detalles de algunos médicos de ejemplo
print(f"\n=== DETALLES DE DISPONIBILIDAD POR MÉDICO (MUESTRA) ===")
for medico in medicos[:5]:  # Mostrar solo los primeros 5 médicos como ejemplo
    print(f"\nMédico: Dr. {medico.usuario.nombres} {medico.usuario.apellidos} - {medico.especialidad.nombre}")
    
    # Disponibilidades regulares
    disp_regulares = DisponibilidadMedica.objects.filter(
        medico=medico, 
        fecha_especial__isnull=True
    ).order_by('dia_semana')
    
    if disp_regulares:
        print("  Disponibilidades regulares:")
        for disp in disp_regulares:
            estado = "ACTIVO" if disp.activo else "INACTIVO"
            print(f"  - {DIAS_SEMANA[disp.dia_semana]}: {disp.hora_inicio.strftime('%H:%M')} - {disp.hora_fin.strftime('%H:%M')} ({disp.tipo_turno}) [{estado}]")
    else:
        print("  No tiene disponibilidades regulares configuradas.")
    
    # Disponibilidades especiales
    disp_especiales = DisponibilidadMedica.objects.filter(
        medico=medico, 
        fecha_especial__isnull=False
    ).order_by('fecha_especial')
    
    if disp_especiales:
        print("  Disponibilidades especiales:")
        for disp in disp_especiales:
            estado = "ACTIVO" if disp.activo else "INACTIVO"
            print(f"  - {disp.fecha_especial.strftime('%d/%m/%Y')}: {disp.hora_inicio.strftime('%H:%M')} - {disp.hora_fin.strftime('%H:%M')} ({disp.tipo_turno}) [{estado}]")
    else:
        print("  No tiene disponibilidades especiales configuradas.")

print("\nVerificación de disponibilidades completada.")
