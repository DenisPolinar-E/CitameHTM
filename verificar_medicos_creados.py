import os
import django

# Configurar entorno Django
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'citame.settings')
django.setup()

# Importar modelos
from core.models import Usuario, Medico, Especialidad

def verificar_medicos_creados():
    """
    Verificar que todos los médicos se crearon correctamente
    """
    
    print("🏥 VERIFICACIÓN DE MÉDICOS CREADOS EN EL HOSPITAL DE TINGO MARÍA")
    print("=" * 70)
    
    # Contar médicos totales
    total_medicos = Medico.objects.count()
    total_usuarios_medicos = Usuario.objects.filter(rol__nombre='Medico').count()
    
    print(f"📊 RESUMEN GENERAL:")
    print(f"   👨‍⚕️ Total de médicos: {total_medicos}")
    print(f"   👤 Total de usuarios con rol médico: {total_usuarios_medicos}")
    
    if total_medicos == total_usuarios_medicos:
        print("   ✅ Consistencia: CORRECTA - Todos los médicos tienen usuario")
    else:
        print("   ❌ Inconsistencia detectada")
    
    print("\n📋 DISTRIBUCIÓN POR ESPECIALIDAD:")
    print("-" * 70)
    
    # Objetivo por especialidad
    objetivos = {
        'Emergencias': 9, 'Medicina General': 13, 'Cuidados Críticos': 5,
        'Obstetricia': 7, 'Ginecología': 4, 'Pediatría': 5, 'Neonatología': 3,
        'Cirugía General': 5, 'Anestesiología': 4, 'Cirugía Digestiva': 2,
        'Cirugía de Cabeza y Cuello': 2, 'Cirugía de Tórax': 1, 'Cirugía Proctológica': 1,
        'Cardiología': 2, 'Neumología': 2, 'Gastroenterología': 2,
        'Dermatología': 1, 'Endocrinología': 1, 'Reumatología': 1,
        'Diagnóstico por Imágenes': 3, 'Patología Clínica': 2, 'Anatomía Patológica': 1,
        'Psicología': 2, 'Nutrición': 1, 'Servicio Social': 2, 'Farmacia': 1,
        'Medicina Física y Rehabilitación': 1, 'Rehabilitación': 2, 'Odontología': 3
    }
    
    total_objetivo = sum(objetivos.values())
    total_alcanzado = 0
    especialidades_completas = 0
    
    for especialidad in Especialidad.objects.all().order_by('nombre'):
        medicos_count = Medico.objects.filter(especialidad=especialidad).count()
        objetivo = objetivos.get(especialidad.nombre, 0)
        
        if medicos_count >= objetivo:
            estado = "✅"
            especialidades_completas += 1
        else:
            estado = "❌"
        
        total_alcanzado += medicos_count
        
        print(f"   {estado} {especialidad.nombre:<35} | {medicos_count:>2}/{objetivo:<2} médicos")
    
    print("-" * 70)
    print(f"📈 ESTADÍSTICAS FINALES:")
    print(f"   🎯 Objetivo total: {total_objetivo} médicos")
    print(f"   ✅ Alcanzado: {total_alcanzado} médicos")
    print(f"   📊 Especialidades completas: {especialidades_completas}/29")
    print(f"   💯 Porcentaje de cumplimiento: {(total_alcanzado/total_objetivo)*100:.1f}%")
    
    # Verificar datos de algunos médicos aleatorios
    print(f"\n🔍 MUESTRA ALEATORIA DE MÉDICOS CREADOS:")
    print("-" * 70)
    
    medicos_muestra = Medico.objects.all()[:5]
    for medico in medicos_muestra:
        usuario = medico.usuario
        print(f"👨‍⚕️ Dr. {usuario.nombres} {usuario.apellidos}")
        print(f"   📋 Especialidad: {medico.especialidad.nombre}")
        print(f"   🆔 DNI: {usuario.dni} | CMP: {medico.cmp}")
        print(f"   📞 Tel: {usuario.telefono} | ✉️ Email: {usuario.email}")
        print(f"   📍 Dirección: {usuario.direccion}")
        print(f"   👤 Sexo: {usuario.sexo} | 📅 Nacimiento: {usuario.fecha_nacimiento}")
        print()
    
    # Verificar distribución por sexo
    medicos_masculinos = Usuario.objects.filter(rol__nombre='Medico', sexo='M').count()
    medicos_femeninos = Usuario.objects.filter(rol__nombre='Medico', sexo='F').count()
    
    print(f"👥 DISTRIBUCIÓN POR SEXO:")
    print(f"   👨 Masculino: {medicos_masculinos} ({(medicos_masculinos/total_usuarios_medicos)*100:.1f}%)")
    print(f"   👩 Femenino: {medicos_femeninos} ({(medicos_femeninos/total_usuarios_medicos)*100:.1f}%)")
    
    print(f"\n🎉 ¡VERIFICACIÓN COMPLETADA!")
    
    if total_alcanzado >= total_objetivo and especialidades_completas == 29:
        print("✅ ¡ÉXITO TOTAL! Todos los médicos fueron creados correctamente")
        print("🏥 El Hospital de Tingo María está completamente equipado")
    else:
        print("⚠️ Algunos objetivos no se alcanzaron completamente")

if __name__ == "__main__":
    verificar_medicos_creados() 