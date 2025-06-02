from datetime import datetime
import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos después de configurar Django
from core.models import Cita, Especialidad

# Parámetros de filtro
fecha_inicio = datetime.strptime('2025-05-02', '%Y-%m-%d').date()
fecha_fin = datetime.strptime('2025-06-01', '%Y-%m-%d').date()
especialidad_nombre = 'Farmacia'

# Buscar el ID de la especialidad
try:
    especialidad = Especialidad.objects.filter(nombre__icontains=especialidad_nombre).first()
    if especialidad:
        especialidad_id = especialidad.id
        print(f"Especialidad encontrada: {especialidad.nombre} (ID: {especialidad_id})")
    else:
        print(f"No se encontró la especialidad '{especialidad_nombre}'")
        especialidad_id = None
        # Listar todas las especialidades disponibles
        print("Especialidades disponibles:")
        for esp in Especialidad.objects.all():
            print(f"- {esp.nombre} (ID: {esp.id})")
except Exception as e:
    print(f"Error al buscar especialidad: {e}")
    especialidad_id = None

# Filtrar citas por fecha
citas = Cita.objects.filter(fecha__range=[fecha_inicio, fecha_fin])
print(f"Total de citas en el rango de fechas: {citas.count()}")

# Aplicar filtro de especialidad si existe
if especialidad_id:
    citas_especialidad = citas.filter(medico__especialidad_id=especialidad_id)
    print(f"Citas para la especialidad '{especialidad_nombre}': {citas_especialidad.count()}")
    
    # Contar citas por estado
    estados = {
        'programada': citas_especialidad.filter(estado='programada').count(),
        'atendida': citas_especialidad.filter(estado='atendida').count(),
        'cancelada': citas_especialidad.filter(estado='cancelada').count(),
        'inasistencia': citas_especialidad.filter(estado='inasistencia').count()
    }
    
    print("Distribución por estado:")
    for estado, cantidad in estados.items():
        print(f"- {estado.capitalize()}: {cantidad}")
else:
    print("No se pudo aplicar el filtro de especialidad")
    
    # Listar todas las citas en el rango de fechas
    print("\nListado de citas en el rango de fechas:")
    for cita in citas[:10]:  # Mostrar solo las primeras 10 para no saturar la salida
        try:
            print(f"- ID: {cita.id}, Fecha: {cita.fecha}, Especialidad: {cita.medico.especialidad.nombre}, Estado: {cita.estado}")
        except:
            print(f"- ID: {cita.id}, Fecha: {cita.fecha}, Estado: {cita.estado}")
    
    if citas.count() > 10:
        print(f"... y {citas.count() - 10} más")
