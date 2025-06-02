// Animación de contador para estadísticas
document.addEventListener('DOMContentLoaded', function() {
    // Verificar si estamos en la página de inicio
    const statsContainer = document.querySelector('.stats-container');
    if (!statsContainer) return;
    
    // Función para animar el contador
    function animateCounters() {
        const statNumbers = document.querySelectorAll('.stat-number');
        
        statNumbers.forEach(statNumber => {
            const targetCount = parseInt(statNumber.getAttribute('data-count'));
            const plusSign = statNumber.textContent.includes('+') ? '+' : '';
            const percentSign = statNumber.textContent.includes('%') ? '%' : '';
            let currentCount = 0;
            
            // Duración de la animación en ms
            const duration = 2000;
            // Intervalo entre cada incremento
            const interval = 20;
            // Incremento por intervalo
            const increment = targetCount / (duration / interval);
            
            const counter = setInterval(() => {
                currentCount += increment;
                
                if (currentCount >= targetCount) {
                    currentCount = targetCount;
                    clearInterval(counter);
                }
                
                // Actualizar el texto con el valor actual
                statNumber.textContent = Math.floor(currentCount) + plusSign + percentSign;
            }, interval);
        });
    }
    
    // Iniciar la animación cuando la sección sea visible
    const observer = new IntersectionObserver((entries) => {
        entries.forEach(entry => {
            if (entry.isIntersecting) {
                animateCounters();
                observer.unobserve(entry.target);
            }
        });
    }, { threshold: 0.2 });
    
    observer.observe(statsContainer);
});
