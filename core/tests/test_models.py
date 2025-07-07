import pytest
from core.models import Medicamento

@pytest.mark.django_db
def test_medicamento_stock_critico():
    med = Medicamento.objects.create(
        codigo='MED001',
        nombre_generico='Paracetamol',
        nombre_comercial='Panadol',
        concentracion='500mg',
        forma_farmaceutica='tableta',
        laboratorio='GSK',
        stock_actual=5,
        stock_minimo=10,
        precio_unitario=1.5,
        fecha_vencimiento='2030-01-01',
    )
    assert med.stock_critico() is True
    med.stock_actual = 15
    med.save()
    assert med.stock_critico() is False 