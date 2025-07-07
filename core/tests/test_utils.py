import pytest
from core.models import Medicamento
from datetime import date, timedelta

@pytest.mark.django_db
def test_medicamento_dias_para_vencer():
    hoy = date.today()
    med = Medicamento.objects.create(
        codigo='MED002',
        nombre_generico='Ibuprofeno',
        nombre_comercial='Advil',
        concentracion='400mg',
        forma_farmaceutica='tableta',
        laboratorio='Pfizer',
        stock_actual=20,
        stock_minimo=5,
        precio_unitario=2.0,
        fecha_vencimiento=hoy + timedelta(days=45),
    )
    dias = med.dias_para_vencer()
    assert dias == 45 