import os
import django
import json

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos necesarios
from django.contrib.auth import get_user_model
from core.models import Rol, Usuario
from core.views import api_dashboard
from rest_framework.test import APIRequestFactory
from rest_framework.request import Request

# Función para simular una solicitud a la API
def test_api_dashboard(username):
    # Obtener el usuario
    User = get_user_model()
    try:
        user = User.objects.get(username=username)
        print(f"Usuario encontrado: {user.username}")
        print(f"Rol del usuario: {user.rol.nombre if user.rol else 'Sin rol'}")
        
        # Crear una solicitud simulada
        factory = APIRequestFactory()
        request = factory.get('/api/dashboard/')
        request.user = user
        
        # Llamar a la API
        response = api_dashboard(request)
        
        # Imprimir la respuesta
        print("\nRespuesta de la API:")
        print(f"Código de estado: {response.status_code}")
        data = response.data
        
        # Imprimir datos de la respuesta
        if 'menu' in data:
            print(f"\nMenú recibido ({len(data['menu'])} elementos):")
            for item in data['menu']:
                print(f"- {item.get('nombre', 'Sin nombre')}")
        else:
            print("No se encontró el menú en la respuesta")
            
        # Guardar la respuesta completa en un archivo JSON para análisis
        with open('admin_menu_response.json', 'w', encoding='utf-8') as f:
            json.dump(data, f, ensure_ascii=False, indent=4)
            print("\nRespuesta completa guardada en 'admin_menu_response.json'")
            
    except User.DoesNotExist:
        print(f"Usuario '{username}' no encontrado")
    except Exception as e:
        print(f"Error: {str(e)}")

# Función para listar todos los usuarios con rol de administrador
def list_admin_users():
    User = get_user_model()
    admin_users = User.objects.filter(rol__nombre__icontains='admin')
    
    print(f"Usuarios con rol de administrador encontrados: {admin_users.count()}")
    for user in admin_users:
        print(f"- {user.username}: {user.rol.nombre}")

# Ejecutar las pruebas
if __name__ == "__main__":
    print("=== Listando usuarios administradores ===")
    list_admin_users()
    
    # Obtener automáticamente el primer usuario administrador
    User = get_user_model()
    admin_users = User.objects.filter(rol__nombre__icontains='admin')
    
    if admin_users.exists():
        admin_username = admin_users.first().username
        print(f"\n=== Probando API para el usuario administrador: {admin_username} ===")
        test_api_dashboard(admin_username)
    else:
        print("\nNo se encontraron usuarios administradores para probar")
