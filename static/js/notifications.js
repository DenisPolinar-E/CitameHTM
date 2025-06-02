// Sistema de notificaciones para el Hospital Tingo María
document.addEventListener('DOMContentLoaded', function() {
    // Ejecutar la limpieza de notificaciones una sola vez al cargar la página
    // Esto evita las solicitudes constantes que generan ruido en la consola
    setTimeout(function() {
        limpiarNotificacionesCitasAtendidas();
    }, 1000); // Retraso de 1 segundo para asegurar que la página esté completamente cargada

    // Nota: Se ha eliminado el intervalo que ejecutaba la limpieza cada 5 segundos
    
    // Actualizar el contador de notificaciones al cargar la página
    updateNotificationCounter();

    // Elementos del DOM
    const btnNotifications = document.getElementById('btnNotifications');
    const notificationsDrawer = document.getElementById('notificationsDrawer');
    const closeNotifications = document.getElementById('closeNotifications');
    const notificationsOverlay = document.getElementById('notificationsOverlay');
    const notificationItems = document.querySelectorAll('.notification-item');
    const notificationLinks = document.querySelectorAll('.notification-link');
    
    if (btnNotifications && notificationsDrawer) {
        // Abrir panel de notificaciones
        btnNotifications.addEventListener('click', function() {
            notificationsDrawer.classList.add('show');
            notificationsOverlay.classList.add('show');
            document.body.style.overflow = 'hidden'; // Prevenir scroll
            
            // Ya no marcamos todas las notificaciones como leídas al abrir el panel
            // Solo actualizamos el contador para reflejar el número real de notificaciones no leídas
            updateNotificationCounter();
        });
    }
    
    // Cerrar panel de notificaciones
    if (closeNotifications) {
        closeNotifications.addEventListener('click', function() {
            notificationsDrawer.classList.remove('show');
            notificationsOverlay.classList.remove('show');
            document.body.style.overflow = '';
        });
    }
    
    // Cerrar al hacer clic en el overlay
    if (notificationsOverlay) {
        notificationsOverlay.addEventListener('click', function() {
            notificationsDrawer.classList.remove('show');
            notificationsOverlay.classList.remove('show');
            document.body.style.overflow = '';
        });
    }
    
    // Manejar clic en notificaciones sin enlace
    notificationItems.forEach(item => {
        if (!item.querySelector('.notification-link')) {
            item.addEventListener('click', function() {
                const notificationId = this.getAttribute('data-notification-id');
                if (notificationId) {
                    marcarNotificacionLeida(notificationId);
                }
            });
        }
    });
    
    // Manejar clic en enlaces de notificaciones
    notificationLinks.forEach(link => {
        link.addEventListener('click', function(e) {
            const notificationId = this.getAttribute('data-notification-id');
            if (notificationId) {
                // No prevenimos el evento predeterminado para permitir la navegación
                // Solo marcamos la notificación como leída
                marcarNotificacionLeida(notificationId);
            }
        });
    });
    
    // Función para marcar una notificación específica como leída
    function marcarNotificacionLeida(notificationId) {
        fetch(`/api/marcar-notificacion-leida/${notificationId}/`, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json',
                'X-CSRFToken': getCookie('csrftoken')
            }
        })
        .then(response => response.json())
        .then(data => {
            if (data.success) {
                // Actualizar UI para mostrar la notificación como leída
                const notificationItem = document.querySelector(`.notification-item[data-notification-id="${notificationId}"]`);
                if (notificationItem) {
                    notificationItem.classList.remove('unread');
                }
                
                // Actualizar contador de notificaciones
                updateNotificationCounter();
            }
        })
        .catch(error => console.error('Error:', error));
    }
    
    // Función para actualizar el contador de notificaciones
    function updateNotificationCounter() {
        fetch('/api/notificaciones-no-leidas-count/', {
            method: 'GET',
            headers: {
                'Content-Type': 'application/json'
            }
        })
        .then(response => response.json())
        .then(data => {
            const badge = document.querySelector('.notification-badge');
            if (badge) {
                if (data.count > 0) {
                    badge.textContent = data.count;
                    badge.style.display = '';
                } else {
                    badge.style.display = 'none';
                }
            }
        })
        .catch(error => console.error('Error:', error));
    }
});

// Función para limpiar notificaciones de citas atendidas
// Esta función ha sido desactivada para evitar solicitudes constantes a la API
function limpiarNotificacionesCitasAtendidas() {
    console.log('Función de limpieza de notificaciones desactivada para evitar solicitudes constantes');
    // La funcionalidad ha sido comentada para evitar solicitudes constantes
    /*
    // Primero, intentamos eliminar notificaciones específicas que sabemos que son problemáticas
    // Buscamos notificaciones que contengan texto específico de citas
    const notificacionesItems = document.querySelectorAll('.notification-item');
    
    notificacionesItems.forEach(item => {
        const texto = item.textContent.toLowerCase();
        const notificationId = item.getAttribute('data-notification-id');
        
        // Si el texto contiene palabras clave de citas agendadas, la eliminamos manualmente
        if (texto.includes('nueva cita agendada') || 
            texto.includes('cita con denis lister') || 
            texto.includes('29/05/2025') || 
            texto.includes('13:00')) {
            
            console.log('Encontrada notificación de cita que debería eliminarse:', texto);
            
            if (notificationId) {
                // Eliminar esta notificación específica
                fetch(`/api/eliminar-notificacion/${notificationId}/`, {
                    method: 'POST',
                    headers: {
                        'Content-Type': 'application/json',
                        'X-CSRFToken': getCookie('csrftoken')
                    },
                })
                .then(response => response.json())
                .then(data => {
                    if (data.success) {
                        console.log(`Notificación ID ${notificationId} eliminada manualmente`);
                        item.remove(); // Eliminar del DOM
                        updateNotificationCounter();
                    }
                })
                .catch(error => console.error('Error:', error));
            }
        }
    });
    
    // Luego, ejecutamos la limpieza normal a través de la API
    fetch('/api/limpiar-notificaciones-citas-atendidas/', {
        method: 'GET',
        headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrftoken')
        },
    })
    .then(response => response.json())
    .then(data => {
        if (data.success && data.eliminadas > 0) {
            console.log(`Se eliminaron ${data.eliminadas} notificaciones de citas atendidas`);
            // Actualizar contador de notificaciones
            updateNotificationCounter();
            // Recargar la página si hay notificaciones eliminadas para refrescar la vista
            if (document.getElementById('notificationsDrawer').classList.contains('show')) {
                location.reload();
            }
        }
    })
    .catch(error => console.error('Error:', error));
    */
}

// Función para obtener el valor de una cookie
function getCookie(name) {
    let cookieValue = null;
    if (document.cookie && document.cookie !== '') {
        const cookies = document.cookie.split(';');
        for (let i = 0; i < cookies.length; i++) {
            const cookie = cookies[i].trim();
            if (cookie.substring(0, name.length + 1) === (name + '=')) {
                cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
                break;
            }
        }
    }
    return cookieValue;
}
