import os
import django
import sys

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

from core.models import Cita
from datetime import datetime

def main():
    # Definir rango de fechas
    start_date = '2025-03-01'
    end_date = '2025-06-01'
    
    print(f"Buscando citas entre {start_date} y {end_date}...")
    
    # Consultar citas
    citas = Cita.objects.filter(fecha__gte=start_date, fecha__lte=end_date)
    
    # Mostrar resultados
    total = citas.count()
    print(f"Total de citas encontradas: {total}")
    
    if total > 0:
        print("\nPrimeras 5 citas:")
        for i, cita in enumerate(citas[:5]):
            print(f"{i+1}. Fecha: {cita.fecha}, Estado: {cita.estado}, Médico: {cita.medico}")
            
        # Contar por estado
        estados = citas.values('estado').distinct()
        print("\nConteo por estado:")
        for estado in estados:
            estado_nombre = estado['estado']
            count = citas.filter(estado=estado_nombre).count()
            print(f"{estado_nombre}: {count}")
    else:
        print("No hay citas en este rango de fechas")
    
    # Verificar total de citas en la base de datos
    total_citas = Cita.objects.all().count()
    print(f"\nTotal de citas en la base de datos: {total_citas}")
    
    if total_citas > 0:
        # Mostrar rango de fechas de todas las citas
        primera_cita = Cita.objects.all().order_by('fecha').first()
        ultima_cita = Cita.objects.all().order_by('-fecha').first()
        
        if primera_cita and ultima_cita:
            print(f"Rango de fechas de todas las citas: {primera_cita.fecha} a {ultima_cita.fecha}")

if __name__ == "__main__":
    main()
