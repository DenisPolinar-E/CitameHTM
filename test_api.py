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
        return token.key
    return None

# Función para probar la API directamente
def test_api_medicos_por_especialidad(especialidad_id, token):
    url = f"http://localhost:8000/api/medicos-por-especialidad/{especialidad_id}/"
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
            print(f"Respuesta: {json.dumps(data, indent=2)}")
            
            if data.get('success'):
                medicos = data.get('medicos', [])
                print(f"Médicos encontrados: {len(medicos)}")
                for medico in medicos:
                    print(f"  - ID: {medico.get('id')}, Nombre: {medico.get('nombres')} {medico.get('apellidos')}")
            else:
                print(f"Error en la respuesta: {data.get('error')}")
        else:
            print(f"Error en la solicitud: {response.text}")
    except Exception as e:
        print(f"Error al realizar la solicitud: {str(e)}")

# Crear un usuario de prueba con rol de paciente si no existe
def ensure_test_user():
    User = get_user_model()
    username = "testpaciente"
    password = "testpassword"
    
    try:
        user = User.objects.get(username=username)
        print(f"Usuario de prueba ya existe: {user.username}")
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

# Ejecutar pruebas
if __name__ == "__main__":
    print("=== PROBANDO API DE MÉDICOS POR ESPECIALIDAD ===")
    
    # Asegurar que existe un usuario de prueba
    username, password = ensure_test_user()
    
    # Obtener token de autenticación
    token = get_auth_token(username, password)
    if not token:
        print("Error: No se pudo obtener token de autenticación")
        exit(1)
    
    print(f"Token obtenido: {token}")
    
    # Probar con todas las especialidades
    especialidades = Especialidad.objects.all()
    for esp in especialidades:
        test_api_medicos_por_especialidad(esp.id, token)
