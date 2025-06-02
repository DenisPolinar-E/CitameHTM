// Script para agregar la opción de Historial Médico al menú lateral del administrador
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si estamos en la página del administrador
    if (document.querySelector('.sidebar-menu')) {
        // Buscar el menú lateral
        const sidebarMenu = document.querySelector('.sidebar-menu');
        
        // Verificar si ya existe la opción de Historial Médico
        const existingHistorialLink = Array.from(sidebarMenu.querySelectorAll('.menu-item')).find(
            item => item.textContent.trim() === 'Historial Médico'
        );
        
        // Si no existe, agregarla después del Dashboard
        if (!existingHistorialLink) {
            const dashboardLink = Array.from(sidebarMenu.querySelectorAll('.menu-item')).find(
                item => item.textContent.trim() === 'Dashboard'
            );
            
            if (dashboardLink) {
                // Crear el nuevo enlace
                const historialLink = document.createElement('a');
                historialLink.href = '/admin/historial-medico/';
                historialLink.className = 'menu-item';
                historialLink.innerHTML = '<i class="fas fa-file-medical-alt"></i> Historial Médico';
                
                // Insertar después del Dashboard
                dashboardLink.insertAdjacentElement('afterend', historialLink);
            }
        }
    }
});
