// Función para marcar notificación como leída
function marcarLeida(notificacionId) {
    // Realizar la petición AJAX para marcar como leída
    fetch('/api/notificaciones/marcar-leida/', {
        method: 'POST',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        },
        body: JSON.stringify({
            notificacion_id: notificacionId
        })
    })
    .then(response => response.json())
    .then(data => {
        if (data.success) {
            // Actualizar la interfaz
            const notificacion = document.getElementById(`notificacion-${notificacionId}`);
            if (notificacion) {
                notificacion.remove();
            }
            // Actualizar contador de notificaciones
            actualizarContadorNotificaciones();
        }
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Función para actualizar el contador de notificaciones
function actualizarContadorNotificaciones() {
    // Obtener el número de notificaciones no leídas
    fetch('/api/notificaciones/contador/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': document.querySelector('[name=csrfmiddlewaretoken]').value
        }
    })
    .then(response => response.json())
    .then(data => {
        // Actualizar el contador en la interfaz
        const contadores = document.querySelectorAll('.notification-badge');
        contadores.forEach(contador => {
            if (data.no_leidas > 0) {
                contador.textContent = data.no_leidas;
                contador.style.display = 'inline-block';
            } else {
                contador.style.display = 'none';
            }
        });
    })
    .catch(error => {
        console.error('Error:', error);
    });
}

// Inicializar gráficos para el dashboard de administrador
function inicializarGraficosAdmin() {
    if (document.getElementById('especialidadesChart')) {
        const especialidadesCtx = document.getElementById('especialidadesChart').getContext('2d');
        const especialidadesLabels = JSON.parse(document.getElementById('especialidadesLabels').textContent);
        const especialidadesData = JSON.parse(document.getElementById('especialidadesData').textContent);
        
        new Chart(especialidadesCtx, {
            type: 'pie',
            data: {
                labels: especialidadesLabels,
                datasets: [{
                    data: especialidadesData,
                    backgroundColor: [
                        '#1976d2',
                        '#388e3c',
                        '#e65100',
                        '#7b1fa2',
                        '#c2185b',
                        '#0097a7',
                        '#fbc02d',
                        '#d32f2f'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                plugins: {
                    legend: {
                        position: 'right',
                    },
                    title: {
                        display: true,
                        text: 'Distribución de citas por especialidad'
                    }
                }
            }
        });
    }

    if (document.getElementById('asistenciaChart')) {
        const asistenciaCtx = document.getElementById('asistenciaChart').getContext('2d');
        const asistenciaLabels = JSON.parse(document.getElementById('asistenciaLabels').textContent);
        const asistenciaData = JSON.parse(document.getElementById('asistenciaData').textContent);
        
        new Chart(asistenciaCtx, {
            type: 'bar',
            data: {
                labels: asistenciaLabels,
                datasets: [{
                    label: 'Asistencia a citas',
                    data: asistenciaData,
                    backgroundColor: [
                        '#4caf50',
                        '#f44336',
                        '#ff9800'
                    ],
                    borderWidth: 1
                }]
            },
            options: {
                responsive: true,
                scales: {
                    y: {
                        beginAtZero: true
                    }
                },
                plugins: {
                    legend: {
                        display: false
                    },
                    title: {
                        display: true,
                        text: 'Estadísticas de asistencia'
                    }
                }
            }
        });
    }
}

// Inicializar cuando el DOM esté cargado
document.addEventListener('DOMContentLoaded', function() {
    // Inicializar gráficos si estamos en el dashboard de administrador
    inicializarGraficosAdmin();
    
    // Agregar event listeners para los botones de marcar notificaciones como leídas
    document.querySelectorAll('.btn-marcar-leida').forEach(button => {
        button.addEventListener('click', function() {
            const notificacionId = this.getAttribute('data-notificacion-id');
            marcarLeida(notificacionId);
        });
    });
    
    // Actualizar contador de notificaciones al cargar la página
    actualizarContadorNotificaciones();
});
