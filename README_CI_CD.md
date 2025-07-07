# 🚀 CI/CD Setup - CitaMe

## 📋 Descripción

Este documento describe la configuración de CI/CD (Integración Continua/Entrega Continua) para el proyecto CitaMe.

## 🛠️ Configuración Rápida

### 1. Configurar Variables de Entorno

Copia el archivo de ejemplo y configura tus variables:

```bash
cp env_example.txt .env
```

Edita `.env` con tus valores reales.

### 2. Ejecutar con Docker

```bash
# Construir y ejecutar
docker-compose up --build

# Solo ejecutar (si ya está construido)
docker-compose up

# Ejecutar en segundo plano
docker-compose up -d
```

### 3. Ejecutar Tests

```bash
# Tests con cobertura
pytest

# Tests específicos
pytest core/tests/test_models.py

# Ver reporte de cobertura
pytest --cov-report=html
```

## 🔧 Configuración de GitHub Actions

### Requisitos Previos

1. **Fork del repositorio** en GitHub
2. **Configurar secrets** en Settings > Secrets and variables > Actions:
   - `SNYK_TOKEN` (opcional, para escaneo de seguridad)

### Workflow Automático

El pipeline se ejecuta automáticamente en:
- **Push** a `main` o `develop`
- **Pull Request** a `main`

### Jobs del Pipeline

1. **Test**: Ejecuta tests y genera reporte de cobertura
2. **Security Scan**: Escanea vulnerabilidades (requiere Snyk)
3. **Deploy Staging**: Despliega a staging (desde `develop`)
4. **Deploy Production**: Despliega a producción (desde `main`)

## 📊 Métricas y Monitoreo

### Cobertura de Tests
- **Objetivo**: 80%+
- **Reporte**: Se genera automáticamente en cada build
- **Visualización**: Codecov (integrado)

### Tiempos de Build
- **Tests**: ~5-10 minutos
- **Security Scan**: ~2-3 minutos
- **Deploy**: ~3-5 minutos

## 🐳 Docker

### Comandos Útiles

```bash
# Construir imagen
docker build -t citame .

# Ejecutar contenedor
docker run -p 8000:8000 citame

# Ver logs
docker-compose logs web

# Ejecutar comandos dentro del contenedor
docker-compose exec web python manage.py migrate
docker-compose exec web python manage.py createsuperuser
```

### Variables de Entorno en Docker

Las variables se configuran en `docker-compose.yml`:

```yaml
environment:
  - SECRET_KEY=your-secret-key
  - DEBUG=True
  - DB_NAME=citame
  - DB_USER=postgres
  - DB_PASSWORD=postgres
```

## 🔒 Seguridad

### Escaneo Automático
- **Snyk**: Análisis de vulnerabilidades en dependencias
- **Bandit**: Análisis estático de código Python
- **Frecuencia**: En cada commit

### Configuración de Seguridad

```python
# settings.py
SECURE_BROWSER_XSS_FILTER = True
SECURE_CONTENT_TYPE_NOSNIFF = True
X_FRAME_OPTIONS = 'DENY'
```

## 📈 Monitoreo

### Herramientas Recomendadas

1. **Sentry**: Manejo de errores
2. **Prometheus**: Métricas de aplicación
3. **Grafana**: Visualización de datos

### Configuración de Sentry

```python
# settings.py
import sentry_sdk
from sentry_sdk.integrations.django import DjangoIntegration

sentry_sdk.init(
    dsn="your-sentry-dsn",
    integrations=[DjangoIntegration()],
    traces_sample_rate=1.0,
    send_default_pii=True
)
```

## 🚨 Troubleshooting

### Problemas Comunes

1. **Tests fallan en CI pero pasan localmente**
   - Verificar variables de entorno
   - Revisar configuración de base de datos

2. **Docker no puede conectarse a PostgreSQL**
   - Verificar que el servicio `db` esté corriendo
   - Revisar variables de entorno de conexión

3. **Cobertura de tests baja**
   - Agregar más tests unitarios
   - Revisar configuración de pytest

### Logs Útiles

```bash
# Logs de GitHub Actions
# Ver en: https://github.com/username/repo/actions

# Logs de Docker
docker-compose logs web
docker-compose logs db

# Logs de Django
docker-compose exec web tail -f /app/logs/django.log
```

## 📞 Soporte

Para problemas con CI/CD:
1. Revisar logs de GitHub Actions
2. Verificar configuración de secrets
3. Consultar documentación de herramientas

---

**Última actualización**: Julio 2025  
**Versión**: 1.0 