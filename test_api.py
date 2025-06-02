import os
import django
import requests
import json
from django.contrib.auth import get_user_model

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos
from core.models import Especialidad, Medico, Usuario, Rol

# Función para obtener un token de autenticación
def get_auth_token(username, password):
    from django.contrib.auth import authenticate
    from rest_framework.authtoken.models import Token
    
    user = authenticate(username=username, password=password)
    if user:
        token, _ = Token.objects.get_or_create(user=user)
        print(f"Token generado para {username}: {token.key}")
        return token.key
    else:
        print(f"Error de autenticación para el usuario {username}")
        return None

# Función para probar la API de médicos por especialidad
def test_api_medicos_por_especialidad(especialidad_id, token):
    # URL correcta según la memoria del sistema
    url = f"http://localhost:8000/api/medicos-por-especialidad/?especialidad_id={especialidad_id}"
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\nProbando API para especialidad ID: {especialidad_id}")
    print(f"URL: {url}")
    print(f"Headers: {headers}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Respuesta:")
            print(json.dumps(data, indent=4, ensure_ascii=False))
            
            # Mostrar información de médicos si está disponible
            medicos = data.get('medicos', [])
            print(f"Médicos encontrados: {len(medicos)}")
            for medico in medicos:
                print(f"  - ID: {medico.get('id')}, Nombre: {medico.get('nombre')}")
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error en la solicitud: {e}")

# Función para probar la API de distribución de citas
def test_api_distribucion_citas(periodo, fecha_inicio, fecha_fin, especialidad_id, token):
    url = f"http://localhost:8000/api/distribucion-citas/?periodo={periodo}&fecha_inicio={fecha_inicio}&fecha_fin={fecha_fin}&especialidad={especialidad_id}"
    
    headers = {
        'Authorization': f'Token {token}',
        'Content-Type': 'application/json'
    }
    
    print(f"\nProbando API de distribución de citas")
    print(f"Filtros: Periodo={periodo}, Fecha inicio={fecha_inicio}, Fecha fin={fecha_fin}, Especialidad ID={especialidad_id}")
    print(f"URL: {url}")
    
    try:
        response = requests.get(url, headers=headers)
        print(f"Status Code: {response.status_code}")
        
        if response.status_code == 200:
            data = response.json()
            print("Respuesta:")
            print(json.dumps(data, indent=4, ensure_ascii=False))
        else:
            print(f"Error: {response.text}")
    except Exception as e:
        print(f"Error en la solicitud: {e}")

# Función para asegurar que existe un usuario de prueba
def ensure_test_user():
    User = get_user_model()
    username = "testuser"
    password = "testpass123"
    
    try:
        user = User.objects.get(username=username)
        print(f"Usuario de prueba ya existe: {username}")
    except User.DoesNotExist:
        # Crear rol de paciente si no existe
        rol, _ = Rol.objects.get_or_create(nombre="Paciente")
        
        # Crear usuario
        user = User.objects.create_user(
            username=username,
            password=password,
            email="test@example.com",
            nombres="Test",
            apellidos="Paciente",
            dni="12345678",
            rol=rol
        )
        print(f"Usuario de prueba creado: {user.username}")
    
    return username, password

# Bloque principal para ejecutar el script
if __name__ == "__main__":
    print("=== PROBANDO APIs DEL SISTEMA ===")
    
    # Asegurar que existe un usuario de prueba
    username, password = ensure_test_user()
    
    # Obtener token de autenticación
    token = get_auth_token(username, password)
    if not token:
        print("Error: No se pudo obtener token de autenticación")
        exit(1)
    
    print(f"Token obtenido: {token}")
    
    # Probar API de médicos por especialidad
    print("\n=== PROBANDO API DE MÉDICOS POR ESPECIALIDAD ===")
    especialidades = Especialidad.objects.all()
    if especialidades.exists():
        for esp in especialidades[:3]:  # Limitar a las primeras 3 especialidades
            test_api_medicos_por_especialidad(esp.id, token)
    else:
        print("No hay especialidades registradas en el sistema")
        # Probar con un ID genérico
        test_api_medicos_por_especialidad("1", token)
    
    # Probar API de distribución de citas
    print("\n=== PROBANDO API DE DISTRIBUCIÓN DE CITAS ===")
    test_api_distribucion_citas(
        periodo="mensual", 
        fecha_inicio="2025-01-01", 
        fecha_fin="2025-12-31", 
        especialidad_id="",  # Sin filtro de especialidad
        token=token
    )
