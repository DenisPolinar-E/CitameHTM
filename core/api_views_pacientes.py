from django.http import JsonResponse
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from .models import Paciente

@login_required
def buscar_pacientes_api(request):
    """
    API para buscar pacientes por nombre, apellido o DNI.
    Devuelve los 10 primeros resultados que coincidan con el término de búsqueda.
    """
    # Verificar que el usuario sea médico
    if not hasattr(request.user, 'medico'):
        return JsonResponse({'error': 'No autorizado'}, status=403)
    
    # Obtener término de búsqueda
    query = request.GET.get('q', '')
    
    if not query or len(query) < 2:
        return JsonResponse([], safe=False)
    
    # Buscar pacientes que coincidan
    pacientes = Paciente.objects.filter(
        Q(usuario__nombres__icontains=query) | 
        Q(usuario__apellidos__icontains=query) |
        Q(usuario__dni__icontains=query)
    ).select_related('usuario')[:10]
    
    # Formatear resultados
    resultados = []
    for paciente in pacientes:
        resultados.append({
            'id': paciente.id,
            'dni': paciente.usuario.dni,
            'nombres': paciente.usuario.nombres,
            'apellidos': paciente.usuario.apellidos,
            'texto': f"{paciente.usuario.nombres} {paciente.usuario.apellidos} - DNI: {paciente.usuario.dni}"
        })
    
    return JsonResponse(resultados, safe=False)
