import random
from datetime import datetime, timedelta, date, time
from django.core.management.base import BaseCommand
from core.models import Paciente, Medico, Especialidad, Cita, Consultorio
from django.db import transaction

# Especialidades permitidas
ESPECIALIDADES_PERMITIDAS = [
    'Emergencias',
    'Medicina General',
    'Nutrición',
    'Obstetricia',
    'Odontología',
    'Psicología',
]

# Diagnósticos comunes y graves por especialidad
DIAGNOSTICOS = {
    'Emergencias': {
        'comunes': [
            'Gripe', 'Dolor abdominal', 'Cefalea', 'Fiebre', 'Herida leve', 'Contusión',
        ],
        'graves': [
            'Infarto agudo de miocardio', 'Accidente cerebrovascular', 'Shock séptico', 'Traumatismo grave',
        ]
    },
    'Medicina General': {
        'comunes': [
            'Resfriado común', 'Gastritis', 'Alergia estacional', 'Hipertensión controlada', 'Lumbalgia',
        ],
        'graves': [
            'Diabetes descompensada', 'Insuficiencia renal aguda', 'Crisis hipertensiva',
        ]
    },
    'Nutrición': {
        'comunes': [
            'Sobrepeso', 'Obesidad grado I', 'Desnutrición leve', 'Anemia leve',
        ],
        'graves': [
            'Desnutrición severa', 'Obesidad mórbida', 'Anemia severa',
        ]
    },
    'Obstetricia': {
        'comunes': [
            'Control prenatal', 'Náuseas en el embarazo', 'Anemia gestacional',
        ],
        'graves': [
            'Preeclampsia', 'Amenaza de aborto', 'Diabetes gestacional',
        ]
    },
    'Odontología': {
        'comunes': [
            'Caries dental', 'Gingivitis', 'Sensibilidad dental',
        ],
        'graves': [
            'Absceso dental', 'Periodontitis avanzada', 'Fractura dental',
        ]
    },
    'Psicología': {
        'comunes': [
            'Ansiedad leve', 'Estrés laboral', 'Insomnio',
        ],
        'graves': [
            'Depresión mayor', 'Trastorno de pánico', 'Riesgo suicida',
        ]
    },
}

ESTADOS = (
    ("confirmada", 0.98),
    ("pendiente", 0.015),
    ("cancelada", 0.005),
)

class Command(BaseCommand):
    help = 'Crea citas médicas realistas para pacientes registrados en 2023.'

    def handle(self, *args, **options):
        random.seed(42)
        total_citas = 0
        citas_derivacion = 0
        citas_por_estado = {"confirmada": 0, "pendiente": 0, "cancelada": 0}
        citas_por_especialidad = {esp: 0 for esp in ESPECIALIDADES_PERMITIDAS}
        pacientes = list(Paciente.objects.filter(usuario__date_joined__year=2023))
        especialidades = {e.nombre: e for e in Especialidad.objects.filter(nombre__in=ESPECIALIDADES_PERMITIDAS)}
        medicos_por_especialidad = {
            esp: list(Medico.objects.filter(especialidad=especialidades[esp]))
            for esp in ESPECIALIDADES_PERMITIDAS
        }
        consultorios = list(Consultorio.objects.all())
        if not consultorios:
            self.stdout.write(self.style.ERROR('No hay consultorios registrados.'))
            return
        if not all(medicos_por_especialidad.values()):
            self.stdout.write(self.style.ERROR('Faltan médicos en alguna especialidad.'))
            return
        with transaction.atomic():
            for paciente in pacientes:
                num_citas = 2 + int(random.random() < 0.3)  # 70% tendrán 2, 30% tendrán 3
                for _ in range(num_citas):
                    especialidad = random.choice(ESPECIALIDADES_PERMITIDAS)
                    medicos = medicos_por_especialidad[especialidad]
                    medico = random.choice(medicos)
                    consultorio = random.choice(consultorios)
                    # Fecha aleatoria en 2023
                    start_date = date(2023, 1, 1)
                    end_date = date(2023, 12, 31)
                    days_range = (end_date - start_date).days
                    cita_date = start_date + timedelta(days=random.randint(0, days_range))
                    # Hora aleatoria entre 8:00 y 18:00
                    hora_inicio = time(hour=random.randint(8, 17), minute=random.choice([0, 15, 30, 45]))
                    hora_fin = (datetime.combine(date.today(), hora_inicio) + timedelta(minutes=30)).time()
                    # Diagnóstico
                    if random.random() < 0.25:
                        diagnostico = random.choice(DIAGNOSTICOS[especialidad]['graves'])
                        requiere_derivacion = True
                        citas_derivacion += 1
                    else:
                        diagnostico = random.choice(DIAGNOSTICOS[especialidad]['comunes'])
                        requiere_derivacion = False
                    # Estado
                    r = random.random()
                    acc = 0
                    for estado, prob in ESTADOS:
                        acc += prob
                        if r < acc:
                            estado_cita = estado
                            break
                    # Crear cita
                    Cita.objects.create(
                        paciente=paciente,
                        medico=medico,
                        consultorio=consultorio,
                        fecha=cita_date,
                        hora_inicio=hora_inicio,
                        hora_fin=hora_fin,
                        estado=estado_cita,
                        motivo=diagnostico,
                    )
                    total_citas += 1
                    citas_por_estado[estado_cita] += 1
                    citas_por_especialidad[especialidad] += 1
        # Estadísticas
        self.stdout.write(self.style.SUCCESS(f"Citas creadas: {total_citas}"))
        self.stdout.write(f"Citas que requieren derivación: {citas_derivacion} ({citas_derivacion/total_citas*100:.1f}%)")
        self.stdout.write("Distribución por estado:")
        for estado, count in citas_por_estado.items():
            self.stdout.write(f"  {estado}: {count} ({count/total_citas*100:.2f}%)")
        self.stdout.write("Distribución por especialidad:")
        for esp, count in citas_por_especialidad.items():
            self.stdout.write(f"  {esp}: {count}") 