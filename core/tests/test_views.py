import pytest
from django.urls import reverse
from django.contrib.auth import get_user_model
from django.test import Client

@pytest.mark.django_db
def test_consumo_medicamentos_view_admin():
    User = get_user_model()
    # Crear usuario administrador
    admin = User.objects.create_user(username='admin', password='admin123', is_superuser=True)
    client = Client()
    client.login(username='admin', password='admin123')
    url = reverse('admin_reporte_consumo_medicamentos')
    response = client.get(url)
    assert response.status_code == 200
    assert b'Consumo de Medicamentos' in response.content 