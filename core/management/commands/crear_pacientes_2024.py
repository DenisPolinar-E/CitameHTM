from django.core.management.base import BaseCommand
from django.contrib.auth.hashers import make_password
from django.utils import timezone
from datetime import datetime, date
import random
from core.models import Usuario, Rol, Paciente

class Command(BaseCommand):
    help = 'Crear 1000 usuarios pacientes registrados en 2024 con datos realistas y sin repetir nombres/DNIs de 2023'

    def add_arguments(self, parser):
        parser.add_argument(
            '--cantidad',
            type=int,
            default=1000,
            help='Cantidad de pacientes a crear (default: 1000)'
        )

    def handle(self, *args, **options):
        cantidad = options['cantidad']
        try:
            rol_paciente = Rol.objects.get(nombre='PACIENTE')
        except Rol.DoesNotExist:
            self.stdout.write(self.style.ERROR('Error: No existe el rol "PACIENTE". Creando el rol...'))
            rol_paciente = Rol.objects.create(nombre='PACIENTE', descripcion='Pacientes del hospital')
            self.stdout.write(self.style.SUCCESS(f'Rol PACIENTE creado con ID: {rol_paciente.id}'))

        # Nombres y apellidos extendidos para mayor variedad
        nombres_masculinos = [
            'Juan', 'Carlos', 'Luis', 'Miguel', 'Jorge', 'Roberto', 'Fernando', 'Ricardo',
            'Eduardo', 'Alberto', 'Manuel', 'Francisco', 'Javier', 'Diego', 'Andrés',
            'Daniel', 'Pablo', 'Sergio', 'Alejandro', 'Mario', 'José', 'Pedro', 'Antonio',
            'David', 'Rafael', 'Gabriel', 'Héctor', 'Víctor', 'Oscar', 'Raúl', 'Felipe',
            'César', 'Alfonso', 'Ignacio', 'Rodrigo', 'Marco', 'Arturo', 'Leonardo',
            'Gustavo', 'Hugo', 'Adrián', 'Emilio', 'Julio', 'Enrique', 'Armando',
            'Ernesto', 'Alfredo', 'Benjamín', 'Cristian', 'Domingo', 'Elías', 'Federico',
            'Matías', 'Tomás', 'Bruno', 'Samuel', 'Emiliano', 'Martín', 'Nicolás', 'Agustín',
            'Santiago', 'Sebastián', 'Valentín', 'Bautista', 'Lautaro', 'Franco', 'Simón', 'Lorenzo'
        ]
        nombres_femeninos = [
            'María', 'Ana', 'Carmen', 'Rosa', 'Isabel', 'Patricia', 'Lucía', 'Elena',
            'Sofia', 'Valeria', 'Camila', 'Daniela', 'Gabriela', 'Natalia', 'Victoria',
            'Claudia', 'Verónica', 'Silvia', 'Mónica', 'Adriana', 'Carolina', 'Diana',
            'Paula', 'Laura', 'Cecilia', 'Beatriz', 'Angélica', 'Martha', 'Teresa',
            'Gloria', 'Ruth', 'Sandra', 'Yolanda', 'Lourdes', 'Rosa María', 'Ana María',
            'María Elena', 'María Teresa', 'María Carmen', 'María Rosa', 'María Isabel',
            'María Patricia', 'María Lucía', 'María Elena', 'María Sofia', 'María Valeria',
            'María Camila', 'María Daniela', 'María Gabriela', 'María Natalia', 'María Victoria',
            'Julieta', 'Renata', 'Josefina', 'Agustina', 'Mía', 'Martina', 'Bianca', 'Florencia',
            'Milagros', 'Ariana', 'Guadalupe', 'Emilia', 'Josefa', 'Malena', 'Lara', 'Amanda'
        ]
        apellidos = [
            'García', 'Rodríguez', 'González', 'Fernández', 'López', 'Martínez', 'Sánchez',
            'Pérez', 'Gómez', 'Martín', 'Jiménez', 'Ruiz', 'Hernández', 'Díaz', 'Moreno',
            'Muñoz', 'Álvarez', 'Romero', 'Alonso', 'Gutiérrez', 'Navarro', 'Torres',
            'Domínguez', 'Vázquez', 'Ramos', 'Gil', 'Ramírez', 'Serrano', 'Blanco',
            'Suárez', 'Molina', 'Morales', 'Ortega', 'Delgado', 'Castro', 'Ortiz',
            'Rubio', 'Marín', 'Sanz', 'Iglesias', 'Medina', 'Cortés', 'Garrido',
            'Castillo', 'Santos', 'Lozano', 'Guerrero', 'Cano', 'Prieto', 'Méndez',
            'Cruz', 'Calvo', 'Gallego', 'Vidal', 'León', 'Herrera', 'Márquez', 'Peña',
            'Flores', 'Vega', 'Reyes', 'Fuentes', 'Carrasco', 'Diez', 'Cabrera',
            'Nieto', 'Aguilar', 'Pascual', 'Santana', 'Herrero', 'Montero', 'Lara',
            'Hidalgo', 'Lorenzo', 'Santiago', 'Duran', 'Benitez', 'Vargas', 'Mora',
            'Vicente', 'Esteban', 'Crespo', 'Soto', 'Velasco', 'Soler', 'Moya',
            'Estrada', 'Parra', 'Bravo', 'Gallardo', 'Rojas', 'Pardo', 'Luna',
            'Salas', 'Palacios', 'Valdez', 'Mendoza', 'Campos', 'Paredes', 'Rivas', 'Salazar'
        ]
        distritos = [
            'Rupa Rupa', 'Daniel Alomía Robles', 'Hermilio Valdizán', 'José Crespo y Castillo',
            'Luyando', 'Mariano Damaso Beraun', 'Pucayacu', 'Castillo Grande', 'Pueblo Nuevo',
            'Aucayacu', 'Honoria', 'Tournavista', 'Yuyapichis', 'Puerto Inca', 'Codo del Pozuzo'
        ]
        direcciones_base = [
            'Jr. Lima', 'Jr. Huánuco', 'Jr. Arequipa', 'Jr. Trujillo', 'Jr. Piura',
            'Av. Principal', 'Av. Central', 'Av. San Martín', 'Av. Bolognesi',
            'Calle Real', 'Calle Comercio', 'Calle San José', 'Calle San Pedro',
            'Pasaje Los Pinos', 'Pasaje San Francisco', 'Urbanización San Juan',
            'Urbanización Los Álamos', 'Urbanización El Bosque', 'Urbanización La Florida',
            'Asentamiento Humano', 'Barrio San Cristóbal', 'Barrio San Antonio'
        ]
        # Obtener DNIs y nombres usados en 2023
        dnis_usados = set(Usuario.objects.filter(rol=rol_paciente, date_joined__year=2023).values_list('dni', flat=True))
        nombres_usados = set(Usuario.objects.filter(rol=rol_paciente, date_joined__year=2023).values_list('nombres', flat=True))
        apellidos_usados = set(Usuario.objects.filter(rol=rol_paciente, date_joined__year=2023).values_list('apellidos', flat=True))
        # Generar fechas de registro distribuidas en 2024
        def generar_fecha_registro_2024():
            mes_weights = {
                1: 5, 2: 5, 3: 5,  # Enero-Marzo: 15%
                4: 7, 5: 7, 6: 6,  # Abril-Junio: 20%
                7: 8, 8: 8, 9: 9,  # Julio-Septiembre: 25%
                10: 12, 11: 12, 12: 16  # Octubre-Diciembre: 40%
            }
            mes = random.choices(list(mes_weights.keys()), weights=list(mes_weights.values()))[0]
            dia = random.randint(1, 28)
            return date(2024, mes, dia)
        def generar_fecha_nacimiento(grupo_edad):
            año_actual = 2024
            if grupo_edad == 'niño':
                año_nacimiento = random.randint(año_actual - 12, año_actual - 1)
            elif grupo_edad == 'adolescente':
                año_nacimiento = random.randint(año_actual - 17, año_actual - 13)
            elif grupo_edad == 'adulto':
                año_nacimiento = random.randint(año_actual - 64, año_actual - 18)
            else:
                año_nacimiento = random.randint(año_actual - 89, año_actual - 65)
            mes = random.randint(1, 12)
            dia = random.randint(1, 28)
            return date(año_nacimiento, mes, dia)
        grupos_edad = {
            'niño': 0.15,
            'adolescente': 0.10,
            'adulto': 0.60,
            'anciano': 0.15
        }
        self.stdout.write(self.style.SUCCESS(f'Iniciando creación de {cantidad} pacientes registrados en 2024...'))
        usuarios_creados = 0
        for i in range(cantidad):
            try:
                grupo_edad = random.choices(list(grupos_edad.keys()), weights=list(grupos_edad.values()))[0]
                sexo = random.choice(['M', 'F'])
                # Generar nombre y apellidos únicos
                intentos = 0
                while True:
                    if sexo == 'M':
                        nombre = random.choice(nombres_masculinos)
                    else:
                        nombre = random.choice(nombres_femeninos)
                    apellido1 = random.choice(apellidos)
                    apellido2 = random.choice(apellidos)
                    nombre_completo = f"{nombre} {apellido1} {apellido2}"
                    if nombre not in nombres_usados and f"{apellido1} {apellido2}" not in apellidos_usados:
                        break
                    intentos += 1
                    if intentos > 10:
                        break  # Si no encuentra único tras 10 intentos, acepta repetido
                # Generar DNI único
                while True:
                    dni = str(random.randint(10000000, 99999999))
                    if dni not in dnis_usados:
                        dnis_usados.add(dni)
                        break
                telefono = '9' + str(random.randint(10000000, 99999999))
                email = f"{nombre.lower()}{random.randint(1, 999)}@gmail.com"
                distrito = random.choice(distritos)
                direccion_base = random.choice(direcciones_base)
                numero = random.randint(1, 999)
                direccion = f"{direccion_base} {numero}, {distrito}, Leoncio Prado, Huánuco, Perú"
                fecha_registro = generar_fecha_registro_2024()
                fecha_nacimiento = generar_fecha_nacimiento(grupo_edad)
                usuario = Usuario.objects.create(
                    username=f"paciente_{dni}",
                    email=email,
                    password=make_password("Onepiece-2000"),
                    nombres=nombre,
                    apellidos=f"{apellido1} {apellido2}",
                    dni=dni,
                    telefono=telefono,
                    direccion=direccion,
                    fecha_nacimiento=fecha_nacimiento,
                    sexo=sexo,
                    rol=rol_paciente,
                    date_joined=datetime.combine(fecha_registro, datetime.min.time()),
                    is_active=True
                )
                Paciente.objects.create(
                    usuario=usuario,
                    estado_reserva='activo'
                )
                usuarios_creados += 1
                if usuarios_creados % 100 == 0:
                    self.stdout.write(self.style.SUCCESS(f'Creados {usuarios_creados} pacientes...'))
            except Exception as e:
                self.stdout.write(self.style.ERROR(f'Error creando paciente {i+1}: {str(e)}'))
                continue
        self.stdout.write(self.style.SUCCESS(f'✅ Proceso completado. Se crearon {usuarios_creados} pacientes registrados en 2024.'))
        # Estadísticas
        self.stdout.write('\n📊 Estadísticas de pacientes creados:')
        usuarios_por_mes = {}
        for usuario in Usuario.objects.filter(rol=rol_paciente, date_joined__year=2024):
            mes = usuario.date_joined.month
            usuarios_por_mes[mes] = usuarios_por_mes.get(mes, 0) + 1
        self.stdout.write('\n📅 Distribución por mes de registro en 2024:')
        for mes in sorted(usuarios_por_mes.keys()):
            nombre_mes = datetime(2024, mes, 1).strftime('%B')
            self.stdout.write(f'   {nombre_mes}: {usuarios_por_mes[mes]} pacientes')
        masculinos = Usuario.objects.filter(rol=rol_paciente, sexo='M', date_joined__year=2024).count()
        femeninos = Usuario.objects.filter(rol=rol_paciente, sexo='F', date_joined__year=2024).count()
        self.stdout.write(f'\n👥 Distribución por sexo:')
        self.stdout.write(f'   Masculino: {masculinos} pacientes')
        self.stdout.write(f'   Femenino: {femeninos} pacientes')
        self.stdout.write(f'\n👶 Distribución por grupo de edad:')
        for grupo, porcentaje in grupos_edad.items():
            cantidad_esperada = int(cantidad * porcentaje)
            self.stdout.write(f'   {grupo.capitalize()}: ~{cantidad_esperada} pacientes ({porcentaje*100:.0f}%)') 