// Flag para controlar operaciones en curso y evitar colisiones
window.graficosEnProceso = {
    dias: false,
    horarios: false,
    especialidades: false
};

// Almacenamos las instancias de los gráficos en variables globales para mejor control
window.graficosDimensionesAdicionales = {
    dias: null,
    horarios: null,
    especialidades: null
};

/**
 * Destruye y reemplaza completamente un canvas para evitar errores de reutilización
 * @param {string} canvasId - El ID del elemento canvas a reemplazar
 * @returns {HTMLCanvasElement|null} - El nuevo elemento canvas o null si hubo error
 */
function reemplazarCanvas(canvasId) {
    try {
        const contenedor = document.getElementById(`${canvasId}-container`);
        if (!contenedor) {
            console.error(`Contenedor para canvas ${canvasId} no encontrado`);
            return null;
        }
        
        // Eliminar canvas antiguo si existe
        const canvasAntiguo = document.getElementById(canvasId);
        if (canvasAntiguo) {
            contenedor.removeChild(canvasAntiguo);
        }
        
        // Crear nuevo canvas
        const nuevoCanvas = document.createElement('canvas');
        nuevoCanvas.id = canvasId;
        nuevoCanvas.height = 300;
        contenedor.appendChild(nuevoCanvas);
        
        console.log(`Canvas ${canvasId} reemplazado exitosamente`);
        return nuevoCanvas;
    } catch (e) {
        console.error(`Error al reemplazar canvas ${canvasId}:`, e);
        return null;
    }
}

/**
 * Destruye cualquier gráfico existente en un canvas para evitar conflictos
 * @param {string} canvasId - El ID del elemento canvas
 */
function destruirGraficoExistente(canvasId) {
    // Si hay una operación en curso para este gráfico, no hacemos nada
    const tipoGrafico = canvasId.replace('grafico-', '');
    if (window.graficosEnProceso[tipoGrafico]) {
        console.log(`Operación en curso para ${canvasId}, ignorando llamada`);
        return;
    }
    
    window.graficosEnProceso[tipoGrafico] = true;
    
    try {
        // Primero intentamos destruir la gráfica usando Chart.js
        if (window.graficosDimensionesAdicionales[tipoGrafico]) {
            console.log(`Destruyendo instancia guardada de gráfico ${tipoGrafico}`);
            window.graficosDimensionesAdicionales[tipoGrafico].destroy();
            window.graficosDimensionesAdicionales[tipoGrafico] = null;
        }
        
        // Luego, para asegurarnos, reemplazamos todo el canvas
        reemplazarCanvas(canvasId);
    } catch (error) {
        console.error(`Error al destruir gráfico en ${canvasId}:`, error);
        // En caso de error, forzamos reemplazo del canvas
        reemplazarCanvas(canvasId);
    } finally {
        // Desactivar flag de operación en curso
        setTimeout(() => {
            window.graficosEnProceso[tipoGrafico] = false;
        }, 100);
    }
}

// Función para actualizar el gráfico por día de la semana
function actualizarGraficoDias(data) {
    console.log('Llamada a actualizarGraficoDias con datos:', data);
    
    // Verificar que los datos de dimensiones adicionales existan
    if (!data || !data.dimensiones_adicionales) {
        console.error('No se encontraron dimensiones adicionales en los datos');
        return;
    }
    
    if (!data.dimensiones_adicionales.dias_semana) {
        console.error('Datos de días de la semana no disponibles');
        return;
    }
    
    // Verificamos si hay datos para cada día
    const diasSemana = data.dimensiones_adicionales.dias_semana;
    console.log('Datos de días de la semana encontrados:', diasSemana);
    
    // Destruir cualquier gráfico existente en este canvas
    destruirGraficoExistente('grafico-dias');
    
    // Si el tab no está activo, no renderizar el gráfico todavía
    const tabDias = document.getElementById('dia-content');
    if (tabDias && !$(tabDias).is(':visible')) {
        console.log('Tab de días no está visible, no renderizamos el gráfico aún');
        return;
    }
    
    const canvas = document.getElementById('grafico-dias');
    if (!canvas) {
        console.error('Canvas con ID grafico-dias no encontrado');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('No se pudo obtener el contexto 2d del canvas grafico-dias');
        return;
    }
    
    // Preparar los datos para el gráfico
    const labels = Object.keys(diasSemana); // lunes, martes, etc.
    
    // Preparar datasets para cada estado
    const datasetPendientes = {
        label: 'Pendientes',
        data: labels.map(dia => diasSemana[dia].pendientes),
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
    };
    
    const datasetConfirmadas = {
        label: 'Confirmadas',
        data: labels.map(dia => diasSemana[dia].confirmadas),
        backgroundColor: 'rgba(255, 193, 7, 0.7)',
        borderColor: 'rgba(255, 193, 7, 1)',
        borderWidth: 1
    };
    
    const datasetAtendidas = {
        label: 'Atendidas',
        data: labels.map(dia => diasSemana[dia].atendidas),
        backgroundColor: 'rgba(40, 167, 69, 0.7)',
        borderColor: 'rgba(40, 167, 69, 1)',
        borderWidth: 1
    };
    
    const datasetCanceladas = {
        label: 'Canceladas',
        data: labels.map(dia => diasSemana[dia].canceladas),
        backgroundColor: 'rgba(220, 53, 69, 0.7)',
        borderColor: 'rgba(220, 53, 69, 1)',
        borderWidth: 1
    };
    
    // Crear el gráfico
    graficoDias = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [datasetPendientes, datasetConfirmadas, datasetAtendidas, datasetCanceladas]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Distribución de Citas por Día de la Semana'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} citas`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Día de la Semana'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de Citas'
                    }
                }
            }
        }
    });
}

// Función para actualizar el gráfico por horario
function actualizarGraficoHorarios(data) {
    console.log('Llamada a actualizarGraficoHorarios con datos:', data);
    
    // Verificar que los datos de dimensiones adicionales existan
    if (!data || !data.dimensiones_adicionales) {
        console.error('No se encontraron dimensiones adicionales en los datos');
        return;
    }
    
    if (!data.dimensiones_adicionales.horarios) {
        console.error('Datos de horarios no disponibles');
        return;
    }
    
    // Verificamos si hay datos para cada horario
    const horarios = data.dimensiones_adicionales.horarios;
    console.log('Datos de horarios encontrados:', horarios);
    
    // Destruir cualquier gráfico existente en este canvas
    destruirGraficoExistente('grafico-horarios');
    
    // Si el tab no está activo, no renderizar el gráfico todavía
    const tabHorarios = document.getElementById('horario-content');
    if (tabHorarios && !$(tabHorarios).is(':visible')) {
        console.log('Tab de horarios no está visible, no renderizamos el gráfico aún');
        return;
    }
    
    const canvas = document.getElementById('grafico-horarios');
    if (!canvas) {
        console.error('Canvas con ID grafico-horarios no encontrado');
        return;
    }
    
    const ctx = canvas.getContext('2d');
    if (!ctx) {
        console.error('No se pudo obtener el contexto 2d del canvas grafico-horarios');
        return;
    }
    
    // Preparar los datos para el gráfico
    const labels = Object.keys(horarios); // mañana, tarde
    
    // Preparar datasets para cada estado
    const datasetPendientes = {
        label: 'Pendientes',
        data: labels.map(horario => horarios[horario].pendientes),
        backgroundColor: 'rgba(54, 162, 235, 0.7)',
        borderColor: 'rgba(54, 162, 235, 1)',
        borderWidth: 1
    };
    
    const datasetConfirmadas = {
        label: 'Confirmadas',
        data: labels.map(horario => horarios[horario].confirmadas),
        backgroundColor: 'rgba(255, 193, 7, 0.7)',
        borderColor: 'rgba(255, 193, 7, 1)',
        borderWidth: 1
    };
    
    const datasetAtendidas = {
        label: 'Atendidas',
        data: labels.map(horario => horarios[horario].atendidas),
        backgroundColor: 'rgba(40, 167, 69, 0.7)',
        borderColor: 'rgba(40, 167, 69, 1)',
        borderWidth: 1
    };
    
    const datasetCanceladas = {
        label: 'Canceladas',
        data: labels.map(horario => horarios[horario].canceladas),
        backgroundColor: 'rgba(220, 53, 69, 0.7)',
        borderColor: 'rgba(220, 53, 69, 1)',
        borderWidth: 1
    };
    
    // Crear el gráfico
    graficoHorarios = new Chart(ctx, {
        type: 'bar',
        data: {
            labels: labels,
            datasets: [datasetPendientes, datasetConfirmadas, datasetAtendidas, datasetCanceladas]
        },
        options: {
            responsive: true,
            plugins: {
                legend: {
                    position: 'top',
                },
                title: {
                    display: true,
                    text: 'Distribución de Citas por Horario'
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            return `${context.dataset.label}: ${context.parsed.y} citas`;
                        }
                    }
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Horario'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Número de Citas'
                    }
                }
            }
        }
    });
}

// Función para imprimir la estructura completa de datos para depuración
function imprimirEstructuraDatos(data) {
    console.log('=== ESTRUCTURA COMPLETA DE DATOS ===');
    console.log('Data principal:', data);
    
    if (data && data.dimensiones_adicionales) {
        console.log('Dimensiones adicionales:', data.dimensiones_adicionales);
        
        if (data.dimensiones_adicionales.dias_semana) {
            console.log('Datos de días de semana:', data.dimensiones_adicionales.dias_semana);
        } else {
            console.warn('No hay datos de días de semana');
        }
        
        if (data.dimensiones_adicionales.horarios) {
            console.log('Datos de horarios:', data.dimensiones_adicionales.horarios);
        } else {
            console.warn('No hay datos de horarios');
        }
    } else {
        console.warn('No hay dimensiones adicionales');
    }
}

// Función para llamar a las funciones de actualización de gráficos
function actualizarGraficosDimensionesAdicionales(data) {
    imprimirEstructuraDatos(data);
    
    if (data && data.dimensiones_adicionales) {
        // Verificamos qué pestaña está activa para solo actualizar ese gráfico
        const tabActivo = $('.nav-tabs .active').attr('id');
        console.log('Tab activo:', tabActivo);
        
        if (tabActivo === 'dia-tab' && data.dimensiones_adicionales.dias_semana) {
            console.log('Actualizando gráfico de días de la semana desde actualizarGraficosDimensionesAdicionales');
            setTimeout(() => { actualizarGraficoDias(data); }, 100);
        } else if (tabActivo === 'horario-tab' && data.dimensiones_adicionales.horarios) {
            console.log('Actualizando gráfico de horarios desde actualizarGraficosDimensionesAdicionales');
            setTimeout(() => { actualizarGraficoHorarios(data); }, 100);
        } else {
            console.log('No se actualiza ninguna gráfica ya que no está activa la pestaña correspondiente');
        }
    } else {
        console.warn('No hay datos de dimensiones adicionales disponibles');
    }
}
