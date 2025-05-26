from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from datetime import datetime, timedelta
from .models import Medico, DisponibilidadMedica, Cita, Consultorio

@login_required
def medicos_por_especialidad(request, especialidad_id):
    """
    Retorna la lista de médicos que pertenecen a una especialidad específica.
    """
    print(f"[DEBUG] Buscando médicos para la especialidad ID: {especialidad_id}")
    try:
        medicos = Medico.objects.filter(especialidad_id=especialidad_id)
        print(f"[DEBUG] Médicos encontrados: {medicos.count()}")
        
        data = [
            {
                'id': medico.id,
                'nombres': medico.usuario.nombres,
                'apellidos': medico.usuario.apellidos,
                'cmp': medico.cmp
            } 
            for medico in medicos
        ]
        print(f"[DEBUG] Datos a devolver: {data}")
        return JsonResponse(data, safe=False)
    except Exception as e:
        print(f"[ERROR] Error en medicos_por_especialidad: {str(e)}")
        return JsonResponse({'error': str(e)}, status=500)

@login_required
def horarios_disponibles(request, medico_id, fecha):
    """
    Retorna los horarios disponibles para un médico en una fecha específica.
    """
    try:
        # Convertir fecha string a objeto date
        fecha_obj = datetime.strptime(fecha, '%Y-%m-%d').date()
        dia_semana = fecha_obj.weekday()
        
        # Buscar disponibilidades para ese día y médico
        disponibilidades = DisponibilidadMedica.objects.filter(
            Q(medico_id=medico_id) & 
            Q(activo=True) & 
            (Q(dia_semana=dia_semana) | Q(fecha_especial=fecha_obj))
        )
        
        # Excluir horarios ya ocupados por citas
        citas_existentes = Cita.objects.filter(
            medico_id=medico_id,
            fecha=fecha_obj
        )
        
        # Obtener consultorio del médico (simplificado para el ejemplo)
        consultorios = Consultorio.objects.all()
        consultorio_default = consultorios[0] if consultorios.exists() else None
        
        # Construir lista de horarios disponibles
        horarios = []
        for d in disponibilidades:
            # Verificar si el horario ya está ocupado
            ocupado = False
            for c in citas_existentes:
                if (c.hora_inicio <= d.hora_inicio < c.hora_fin) or \
                   (c.hora_inicio < d.hora_fin <= c.hora_fin) or \
                   (d.hora_inicio <= c.hora_inicio and d.hora_fin >= c.hora_fin):
                    ocupado = True
                    break
            
            if not ocupado:
                horarios.append({
                    'id': d.id,
                    'hora_inicio': d.hora_inicio.strftime('%H:%M'),
                    'hora_fin': d.hora_fin.strftime('%H:%M'),
                    'consultorio': consultorio_default.codigo if consultorio_default else '101'
                })
        
        return JsonResponse(horarios, safe=False)
    
    except Exception as e:
        return JsonResponse({'error': str(e)}, status=400)
