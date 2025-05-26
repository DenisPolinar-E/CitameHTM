import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos
from core.models import Especialidad, Medico, Usuario

def verificar_medicos():
    """Verificar y corregir problemas con los médicos y especialidades"""
    print("\n=== VERIFICANDO MÉDICOS Y ESPECIALIDADES ===")
    
    # 1. Verificar especialidades
    especialidades = Especialidad.objects.all()
    print(f"Especialidades encontradas: {especialidades.count()}")
    for esp in especialidades:
        print(f"ID: {esp.id}, Nombre: {esp.nombre}")
    
    # 2. Verificar médicos
    medicos = Medico.objects.all()
    print(f"\nMédicos encontrados: {medicos.count()}")
    for med in medicos:
        try:
            print(f"ID: {med.id}, Nombre: {med.usuario.nombres} {med.usuario.apellidos}, Especialidad: {med.especialidad.nombre} (ID: {med.especialidad.id})")
        except Exception as e:
            print(f"Error al mostrar médico ID {med.id}: {str(e)}")
    
    # 3. Verificar relaciones entre médicos y especialidades
    print("\nVerificando relaciones entre médicos y especialidades...")
    for esp in especialidades:
        medicos_esp = Medico.objects.filter(especialidad=esp)
        print(f"Especialidad: {esp.nombre} (ID: {esp.id}) - {medicos_esp.count()} médicos")
        
        # Verificar que cada médico tenga un usuario válido
        for med in medicos_esp:
            try:
                usuario = med.usuario
                if not usuario.nombres or not usuario.apellidos:
                    print(f"  - ADVERTENCIA: Médico ID {med.id} tiene datos de usuario incompletos")
                    # Corregir datos si es necesario
                    if not usuario.nombres:
                        usuario.nombres = f"Médico{med.id}"
                        usuario.save()
                        print(f"    - Corregido: Asignado nombre '{usuario.nombres}'")
                    if not usuario.apellidos:
                        usuario.apellidos = f"Apellido{med.id}"
                        usuario.save()
                        print(f"    - Corregido: Asignado apellido '{usuario.apellidos}'")
            except Exception as e:
                print(f"  - ERROR: Médico ID {med.id} tiene un problema con su usuario: {str(e)}")

def crear_medico_odontologia():
    """Crear un médico de odontología si no existe ninguno"""
    # Verificar si ya existe un médico de odontología
    try:
        odontologia = Especialidad.objects.get(nombre="Odontología")
        medicos = Medico.objects.filter(especialidad=odontologia)
        
        if medicos.exists():
            print(f"\nYa existen {medicos.count()} médicos de Odontología")
            return
        
        # Crear un usuario para el médico
        usuario = Usuario.objects.create_user(
            username="odontologia1",
            password="password123",
            email="odontologia@hospital.com",
            nombres="Carlos",
            apellidos="Dentista",
            dni="87654321"
        )
        
        # Asignar rol de médico
        from core.models import Rol
        rol, _ = Rol.objects.get_or_create(nombre="Medico")
        usuario.rol = rol
        usuario.save()
        
        # Crear el médico
        medico = Medico.objects.create(
            usuario=usuario,
            especialidad=odontologia,
            cmp="ODONT-001"
        )
        
        print(f"\nCreado nuevo médico de Odontología: {medico}")
        
    except Especialidad.DoesNotExist:
        print("\nNo existe la especialidad de Odontología")
        # Crear la especialidad si no existe
        odontologia = Especialidad.objects.create(
            nombre="Odontología",
            descripcion="Especialidad dedicada a la salud dental",
            acceso_directo=True
        )
        print(f"Creada especialidad de Odontología con ID: {odontologia.id}")
        # Llamar recursivamente para crear el médico
        crear_medico_odontologia()

if __name__ == "__main__":
    verificar_medicos()
    crear_medico_odontologia()
    print("\nVerificación y corrección completada.")
