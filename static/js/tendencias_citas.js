/**
 * tendencias_citas.js - Script para la visualización de tendencias de citas médicas
 * Este script maneja la carga, procesamiento y visualización de datos de tendencias
 * en un gráfico utilizando Chart.js
 */

// Variable global para el gráfico de tendencias
let tendenciasChart = null;

// Colores para los estados de citas
const COLORES_ESTADOS = {
    'pendiente': '#FFC107', // Amarillo
    'confirmada': '#2196F3', // Azul
    'atendida': '#4CAF50',   // Verde
    'cancelada': '#F44336'   // Rojo
};

/**
 * Función para cargar Chart.js dinámicamente si no está disponible
 * @param {Function} callback - Función a ejecutar cuando Chart.js esté disponible
 */
function cargarChartJS(callback) {
    // Si Chart ya está disponible, ejecutar callback inmediatamente
    if (typeof Chart !== 'undefined') {
        console.log('Chart.js ya está disponible');
        callback();
        return;
    }
    
    console.log('Chart.js no está disponible, cargando dinámicamente...');
    
    // Cargar Chart.js dinámicamente
    const script = document.createElement('script');
    script.src = 'https://cdn.jsdelivr.net/npm/chart.js@3.7.1/dist/chart.min.js';
    script.onload = function() {
        console.log('Chart.js cargado correctamente');
        
        // Cargar plugins necesarios
        const annotationScript = document.createElement('script');
        annotationScript.src = 'https://cdn.jsdelivr.net/npm/chartjs-plugin-annotation@1.4.0/dist/chartjs-plugin-annotation.min.js';
        annotationScript.onload = function() {
            console.log('Plugin de anotaciones cargado');
            
            const trendlineScript = document.createElement('script');
            trendlineScript.src = 'https://cdn.jsdelivr.net/npm/chartjs-plugin-trendline';
            trendlineScript.onload = function() {
                console.log('Plugin de trendline cargado');
                callback();
            };
            document.head.appendChild(trendlineScript);
        };
        document.head.appendChild(annotationScript);
    };
    script.onerror = function() {
        console.error('Error al cargar Chart.js');
        document.getElementById('no-data').classList.remove('d-none');
        document.getElementById('no-data').innerHTML = `
            <div class="alert alert-danger">
                <i class="fas fa-exclamation-triangle"></i> 
                Error al cargar las bibliotecas necesarias. Por favor, verifique su conexión a internet y recargue la página.
            </div>`;
    };
    document.head.appendChild(script);
}

/**
 * Inicializar la aplicación una vez que el DOM esté cargado
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('DOM cargado - Inicializando módulo de tendencias');
    
    // Configurar eventos de la interfaz
    setupEventListeners();
    
    // Cargar Chart.js y luego inicializar la aplicación
    cargarChartJS(function() {
        // Inicializar fechas por defecto
        inicializarFechas();
        
        // Cargar médicos por especialidad
        const especialidadSelect = document.getElementById('especialidad');
        if (especialidadSelect) {
            cargarMedicos(especialidadSelect.value);
        }
        
        // Cargar datos iniciales
        cargarTendencias();
    });
});

/**
 * Configura los event listeners para los elementos de la interfaz
 */
function setupEventListeners() {
    // Botón de filtrar
    const btnFiltrar = document.getElementById('btn-filtrar');
    if (btnFiltrar) {
        btnFiltrar.addEventListener('click', function() {
            cargarTendencias();
        });
    }
    
    // Selector de especialidad
    const especialidadSelect = document.getElementById('especialidad');
    if (especialidadSelect) {
        especialidadSelect.addEventListener('change', function() {
            cargarMedicos(this.value);
        });
    }
    
    // Botón de seleccionar todos los estados
    const btnSeleccionarTodos = document.getElementById('btn-seleccionar-todos');
    if (btnSeleccionarTodos) {
        btnSeleccionarTodos.addEventListener('click', function() {
            const estadosSelect = document.getElementById('estados');
            const allSelected = Array.from(estadosSelect.options).every(option => option.selected);
            
            // Cambiar el texto del botón según el estado actual
            if (allSelected) {
                // Deseleccionar todos
                Array.from(estadosSelect.options).forEach(option => option.selected = false);
                this.innerHTML = '<i class="fas fa-check-square mr-1"></i> Seleccionar Todos';
                this.classList.remove('btn-secondary');
                this.classList.add('btn-outline-secondary');
            } else {
                // Seleccionar todos
                Array.from(estadosSelect.options).forEach(option => option.selected = true);
                this.innerHTML = '<i class="fas fa-times-circle mr-1"></i> Deseleccionar Todos';
                this.classList.remove('btn-outline-secondary');
                this.classList.add('btn-secondary');
            }
        });
    }
}

/**
 * Inicializa las fechas por defecto (último mes)
 */
function inicializarFechas() {
    const hoy = new Date();
    const unMesAtras = new Date();
    unMesAtras.setMonth(unMesAtras.getMonth() - 1);
    
    const fechaFin = document.getElementById('fecha_fin');
    const fechaInicio = document.getElementById('fecha_inicio');
    
    if (fechaFin && !fechaFin.value) {
        fechaFin.value = formatearFecha(hoy);
    }
    
    if (fechaInicio && !fechaInicio.value) {
        fechaInicio.value = formatearFecha(unMesAtras);
    }
}

/**
 * Formatea una fecha como YYYY-MM-DD
 * @param {Date} fecha - Objeto Date a formatear
 * @returns {string} Fecha formateada
 */
function formatearFecha(fecha) {
    const year = fecha.getFullYear();
    const month = String(fecha.getMonth() + 1).padStart(2, '0');
    const day = String(fecha.getDate()).padStart(2, '0');
    return `${year}-${month}-${day}`;
}

/**
 * Obtiene los filtros seleccionados por el usuario
 * @returns {Object} Objeto con los filtros
 */
function obtenerFiltros() {
    const fechaInicio = document.getElementById('fecha_inicio').value;
    const fechaFin = document.getElementById('fecha_fin').value;
    const especialidadId = document.getElementById('especialidad').value;
    const medicoId = document.getElementById('medico').value;
    const agrupacion = document.getElementById('agrupacion').value;
    
    // Obtener estados seleccionados (multiselect)
    const estadosSelect = document.getElementById('estados');
    const estados = [];
    
    if (estadosSelect) {
        for (let i = 0; i < estadosSelect.options.length; i++) {
            if (estadosSelect.options[i].selected) {
                estados.push(estadosSelect.options[i].value);
            }
        }
    }
    
    return {
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        especialidad_id: especialidadId,
        medico_id: medicoId,
        agrupacion: agrupacion,
        estados: estados.join(',')
    };
}

/**
 * Valida que las fechas de los filtros sean correctas
 * @param {Object} filtros - Objeto con los filtros
 * @returns {boolean} True si las fechas son válidas
 */
function validarFechas(filtros) {
    if (!filtros.fecha_inicio || !filtros.fecha_fin) {
        alert('Por favor, seleccione ambas fechas');
        return false;
    }
    
    const inicio = new Date(filtros.fecha_inicio);
    const fin = new Date(filtros.fecha_fin);
    
    if (isNaN(inicio.getTime()) || isNaN(fin.getTime())) {
        alert('Las fechas ingresadas no son válidas');
        return false;
    }
    
    if (inicio > fin) {
        alert('La fecha de inicio debe ser anterior a la fecha fin');
        return false;
    }
    
    return true;
}

/**
 * Carga médicos según la especialidad seleccionada
 * @param {string} especialidadId - ID de la especialidad
 */
function cargarMedicos(especialidadId) {
    // Si no hay especialidad seleccionada o es "todas", vaciar y deshabilitar
    if (!especialidadId || especialidadId === '0') {
        const medicoSelect = document.getElementById('medico');
        medicoSelect.innerHTML = '<option value="0">Todos</option>';
        return;
    }
    
    // Mostrar estado de carga
    const medicoSelect = document.getElementById('medico');
    medicoSelect.innerHTML = '<option value="0">Cargando...</option>';
    medicoSelect.disabled = true;
    
    // Hacer petición AJAX para obtener médicos por especialidad
    fetch(`/api/medicos-por-especialidad/?especialidad_id=${especialidadId}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status}`);
            }
            return response.json();
        })
        .then(data => {
            // Llenar selector de médicos
            medicoSelect.innerHTML = '<option value="0">Todos</option>';
            
            if (data && data.medicos && data.medicos.length > 0) {
                data.medicos.forEach(medico => {
                    const option = document.createElement('option');
                    option.value = medico.id;
                    option.textContent = medico.nombre;
                    medicoSelect.appendChild(option);
                });
            }
            
            medicoSelect.disabled = false;
        })
        .catch(error => {
            console.error('Error al cargar médicos:', error);
            medicoSelect.innerHTML = '<option value="0">Error al cargar médicos</option>';
            medicoSelect.disabled = false;
        });
}

/**
 * Actualiza el gráfico de tendencias con los datos recibidos
 * @param {Object} data - Datos para el gráfico de tendencias
 */
function actualizarGraficoTendencias(data) {
    // Verificar que Chart.js esté cargado
    if (typeof Chart === 'undefined') {
        console.error('Error: Chart.js no está disponible');
        document.getElementById('no-data').classList.remove('d-none');
        document.getElementById('no-data').innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Error: Chart.js no está cargado. Por favor, recargue la página.</div>`;
        return;
    }
    
    try {
        // Validar que la estructura de datos sea correcta
        if (!data || !data.fechas || !Array.isArray(data.fechas) || !data.valores_por_estado) {
            console.warn('Estructura de datos inválida para el gráfico');
            document.getElementById('no-data').classList.remove('d-none');
            document.getElementById('no-data').innerHTML = `<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> Los datos recibidos no tienen el formato esperado</div>`;
            return;
        }
        
        // Preparar conjuntos de datos para el gráfico
        const datasets = [];
        const ctx = document.getElementById('tendencias-chart').getContext('2d');
        
        // Crear dataset para cada estado
        Object.keys(data.valores_por_estado).forEach(estado => {
            // Verificar que el estado tenga un color definido
            if (!COLORES_ESTADOS[estado]) {
                console.warn(`No hay color definido para el estado: ${estado}`);
                return;
            }
            
            // Crear dataset
            datasets.push({
                label: estado.charAt(0).toUpperCase() + estado.slice(1),
                data: data.valores_por_estado[estado],
                borderColor: COLORES_ESTADOS[estado],
                backgroundColor: COLORES_ESTADOS[estado] + '20', // 20 es alpha (12%)
                fill: true,
                tension: 0.4,
                pointRadius: 3,
                pointHoverRadius: 5,
                borderWidth: 2
            });
        });
        
        // Verificar si hay datasets para mostrar
        if (datasets.length === 0) {
            console.warn('No hay datos válidos para mostrar en el gráfico');
            document.getElementById('no-data').classList.remove('d-none');
            document.getElementById('no-data').innerHTML = `<div class="alert alert-info"><i class="fas fa-info-circle"></i> No hay datos para mostrar con los filtros seleccionados</div>`;
            return;
        }
        
        // Crear nuevo gráfico
        tendenciasChart = new Chart(ctx, {
            type: 'line',
            data: {
                labels: data.fechas,
                datasets: datasets
            },
            options: {
                responsive: true,
                maintainAspectRatio: false,
                plugins: {
                    title: {
                        display: true,
                        text: 'Evolución de Citas por Estado',
                        font: {
                            size: 16
                        }
                    },
                    legend: {
                        position: 'bottom',
                        labels: {
                            usePointStyle: true,
                            padding: 15
                        }
                    },
                    tooltip: {
                        mode: 'index',
                        intersect: false,
                        callbacks: {
                            label: function(context) {
                                let label = context.dataset.label || '';
                                if (label) {
                                    label += ': ';
                                }
                                if (context.parsed.y !== null) {
                                    label += context.parsed.y;
                                }
                                return label;
                            }
                        }
                    }
                },
                scales: {
                    x: {
                        title: {
                            display: true,
                            text: data.agrupacion.charAt(0).toUpperCase() + data.agrupacion.slice(1)
                        },
                        grid: {
                            display: false
                        }
                    },
                    y: {
                        beginAtZero: true,
                        title: {
                            display: true,
                            text: 'Cantidad de Citas'
                        },
                        ticks: {
                            precision: 0
                        }
                    }
                }
            }
        });
    } catch (error) {
        console.error('Error al actualizar gráfico de tendencias:', error);
        document.getElementById('no-data').classList.remove('d-none');
        document.getElementById('no-data').innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Error al crear gráfico: ${error.message || 'Error desconocido'}</div>`;
    }
}

/**
 * Actualiza las métricas con los datos recibidos
 * @param {Object} data - Datos con métricas
 */
function actualizarMetricas(data) {
    try {
        // Mostrar métricas principales
        if (data && data.metricas) {
            // Tasa de atención
            const tasaAtencion = document.getElementById('tasa-atencion');
            if (tasaAtencion) {
                tasaAtencion.textContent = data.metricas.tasa_atencion + '%';
            }
            
            // Tasa de cancelación
            const tasaCancelacion = document.getElementById('tasa-cancelacion');
            if (tasaCancelacion) {
                tasaCancelacion.textContent = data.metricas.tasa_cancelacion + '%';
            }
            
            // Tendencia mensual
            const tendenciaMensual = document.getElementById('tendencia-mensual');
            if (tendenciaMensual) {
                tendenciaMensual.textContent = formatearTendencia(data.metricas.tendencia_mensual);
            }
            
            // Total de citas
            const totalCitas = document.getElementById('total-citas');
            if (totalCitas) {
                totalCitas.textContent = data.metricas.total_citas;
            }
        } else {
            // Si no hay métricas, mostrar guiones
            const elementos = ['tasa-atencion', 'tasa-cancelacion', 'tendencia-mensual', 'total-citas'];
            elementos.forEach(id => {
                const elemento = document.getElementById(id);
                if (elemento) {
                    elemento.textContent = '-';
                }
            });
            
            console.warn('No hay métricas disponibles en los datos recibidos');
        }
    } catch (error) {
        console.error('Error al actualizar métricas:', error);
    }
}

/**
 * Formatea un valor de tendencia con signo y porcentaje
 * @param {number} valor - Valor de tendencia
 * @returns {string} Tendencia formateada
 */
function formatearTendencia(valor) {
    if (valor === 0) return '0%';
    
    const signo = valor > 0 ? '+' : '';
    return signo + valor + '%';
}

/**
 * Carga los datos de tendencias y actualiza el gráfico
 */
function cargarTendencias() {
    // Obtener valores de filtros
    const fechaInicio = document.getElementById('fecha_inicio').value;
    const fechaFin = document.getElementById('fecha_fin').value;
    const especialidadId = document.getElementById('especialidad').value;
    const medicoId = document.getElementById('medico').value;
    const agrupacion = document.getElementById('agrupacion').value;

    // Obtener estados seleccionados
    const estadosSelect = document.getElementById('estados');
    const estadosSeleccionados = Array.from(estadosSelect.selectedOptions)
        .map(option => option.value);

    // Validar fechas
    if (!fechaInicio || !fechaFin) {
        alert('Por favor, seleccione fechas de inicio y fin.');
        return;
    }

    // Mostrar carga
    document.getElementById('loading').classList.remove('d-none');
    document.getElementById('no-data').classList.add('d-none');
    document.getElementById('tendencias-container').classList.add('d-none');

    // Construir URL con parámetros
    const params = new URLSearchParams({
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin,
        especialidad_id: especialidadId,
        medico_id: medicoId,
        agrupacion: agrupacion,
        estados: estadosSeleccionados.join(',')
    });

    // Realizar petición AJAX
    console.log('Solicitando datos de tendencias:', `/api/tendencias-citas/?${params.toString()}`)

    fetch(`/api/tendencias-citas/?${params.toString()}`)
        .then(response => {
            if (!response.ok) {
                throw new Error(`Error HTTP: ${response.status} - ${response.statusText}`);
            }
            return response.json();
        })
        .then(data => {
            // Guardar datos
            chartData = data;
            console.log('Datos de tendencias recibidos:', data);
            
            // Ocultar carga
            document.getElementById('loading').classList.add('d-none');
            
            // Verificar si hay datos y que la estructura sea correcta
            if (!data.fechas || data.fechas.length === 0 || !data.valores_por_estado) {
                console.warn('No hay datos o estructura incorrecta en la respuesta:', data);
                document.getElementById('no-data').classList.remove('d-none');
                return;
            }
            
            // Mostrar contenedor y actualizar gráfico
            document.getElementById('tendencias-container').classList.remove('d-none');
            actualizarGraficoTendencias(data);
            actualizarMetricas(data);
        })
        .catch(error => {
            console.error('Error al cargar tendencias:', error);
            document.getElementById('loading').classList.add('d-none');
            document.getElementById('no-data').classList.remove('d-none');
            document.getElementById('no-data').innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Error al cargar los datos: ${error.message || 'Error desconocido'}</div>`;
        });
}

/**
 * Actualiza el gráfico de tendencias con los datos recibidos
 * @param {Object} data - Datos para el gráfico de tendencias
 */
function actualizarGraficoTendencias(data) {
    // Verificar que Chart.js esté cargado
    if (typeof Chart === 'undefined') {
        console.error('Error: Chart.js no está disponible');
        document.getElementById('no-data').classList.remove('d-none');
        document.getElementById('no-data').innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Error: Chart.js no está cargado. Por favor, recargue la página.</div>`;
        return;
    }
    try {
        // Validar que la estructura de datos sea correcta
        if (!data || !data.fechas || !Array.isArray(data.fechas) || !data.valores_por_estado) {
            console.error('Estructura de datos incorrecta para el gráfico:', data);
            document.getElementById('no-data').classList.remove('d-none');
            document.getElementById('no-data').innerHTML = `<div class="alert alert-warning"><i class="fas fa-exclamation-triangle"></i> No se pueden mostrar las tendencias: formato de datos incorrecto</div>`;
            return;
        }
        
        // Destruir gráfico anterior si existe
        if (tendenciasChart) {
            tendenciasChart.destroy();
        }
        
        // Obtener el canvas
        const ctx = document.getElementById('tendencias-chart').getContext('2d');
        
        // Preparar datasets
        const datasets = [];
        
        // Preparar dataset para cada estado
        Object.keys(data.valores_por_estado).forEach(estado => {
            // Verificar si hay datos para este estado y que sea un array válido
            if (data.valores_por_estado[estado] && Array.isArray(data.valores_por_estado[estado])) {
                // Verificar que el color existe para este estado, si no usar uno predeterminado
                const color = COLORES_ESTADOS[estado] || '#999999';
                
                datasets.push({
                    label: formatearEstado(estado),
                    data: data.valores_por_estado[estado],
                    borderColor: color,
                    backgroundColor: hexToRgba(color, 0.1),
                    borderWidth: 2,
                    tension: 0.3,
                    fill: false,
                    pointRadius: 3,
                    pointHoverRadius: 5,
                    trendlineLinear: {
                        style: hexToRgba(color, 0.6),
                        lineStyle: "dotted",
                        width: 2
                    }
                });
            }
        });
        
        // Verificar si hay datasets para mostrar
        if (datasets.length === 0) {
            console.warn('No hay datos válidos para mostrar en el gráfico');
            document.getElementById('no-data').classList.remove('d-none');
            document.getElementById('no-data').innerHTML = `<div class="alert alert-info"><i class="fas fa-info-circle"></i> No hay datos para mostrar con los filtros seleccionados</div>`;
            return;
        }
        
        // Crear nuevo gráfico
        tendenciasChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: data.fechas,
            datasets: datasets
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            interaction: {
                mode: 'index',
                intersect: false,
            },
            plugins: {
                title: {
                    display: true,
                    text: 'Evolución de Citas por Estado',
                    font: {
                        size: 18
                    }
                },
                tooltip: {
                    enabled: true,
                    mode: 'index',
                    callbacks: {
                        label: function(context) {
                            let label = context.dataset.label || '';
                            if (label) {
                                label += ': ';
                            }
                            label += context.parsed.y;
                            return label;
                        }
                    }
                },
                legend: {
                    position: 'bottom'
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: obtenerTextoAgrupacion()
                    },
                    grid: {
                        display: false
                    }
                },
                y: {
                    title: {
                        display: true,
                        text: 'Número de Citas'
                    },
                    beginAtZero: true,
                    grid: {
                        color: 'rgba(0, 0, 0, 0.05)'
                    }
                }
            }
        }
    });
    } catch (error) {
        console.error('Error al actualizar gráfico de tendencias:', error);
        document.getElementById('no-data').classList.remove('d-none');
        document.getElementById('no-data').innerHTML = `<div class="alert alert-danger"><i class="fas fa-exclamation-triangle"></i> Error al crear gráfico: ${error.message || 'Error desconocido'}</div>`;
    }
}

/**
 * Actualiza las métricas con los datos recibidos
 * @param {Object} data - Datos con métricas
 */
function actualizarMetricas(data) {
    try {
        // Mostrar métricas principales
        if (data && data.metricas) {
            // Tasa de atención
            const tasaAtencion = document.getElementById('tasa-atencion');
            if (tasaAtencion) {
                tasaAtencion.textContent = data.metricas.tasa_atencion + '%';
            }
            
            // Tasa de cancelación
            const tasaCancelacion = document.getElementById('tasa-cancelacion');
            if (tasaCancelacion) {
                tasaCancelacion.textContent = data.metricas.tasa_cancelacion + '%';
            }
            
            // Tendencia mensual
            const tendenciaMensual = document.getElementById('tendencia-mensual');
            if (tendenciaMensual) {
                tendenciaMensual.textContent = formatearTendencia(data.metricas.tendencia_mensual);
            }
            
            // Total de citas
            const totalCitas = document.getElementById('total-citas');
            if (totalCitas) {
                totalCitas.textContent = data.metricas.total_citas;
            }
        } else {
            // Si no hay métricas, mostrar guiones
            const elementos = ['tasa-atencion', 'tasa-cancelacion', 'tendencia-mensual', 'total-citas'];
            elementos.forEach(id => {
                const elemento = document.getElementById(id);
                if (elemento) {
                    elemento.textContent = '-';
                }
            });
            
            console.warn('No hay métricas disponibles en los datos recibidos');
        }
    } catch (error) {
        console.error('Error al actualizar métricas:', error);
    }
}

/**
 * Formatea el texto para la tendencia mensual
 * @param {number} tendencia - Valor de tendencia (+/-)
 * @returns {string} Texto formateado
 */
function formatearTendencia(tendencia) {
    if (!tendencia) return '-';
    
    const valor = Math.abs(tendencia);
    const simbolo = tendencia > 0 ? '+' : '-';
    
    return simbolo + valor + '%';
}

/**
 * Formatea el nombre del estado para mostrar
 * @param {string} estado - Estado en minúsculas
 * @returns {string} Estado formateado
 */
function formatearEstado(estado) {
    const formateo = {
        'pendiente': 'Pendientes',
        'confirmada': 'Confirmadas',
        'atendida': 'Atendidas',
        'cancelada': 'Canceladas'
    };
    
    return formateo[estado] || estado;
}

/**
 * Obtiene el texto para el eje X según la agrupación
 * @returns {string} Texto de agrupación
 */
function obtenerTextoAgrupacion() {
    const agrupacion = document.getElementById('agrupacion').value;
    
    switch(agrupacion) {
        case 'dia': return 'Día';
        case 'semana': return 'Semana';
        case 'mes': return 'Mes';
        default: return 'Período';
    }
}

/**
 * Convierte color hexadecimal a formato RGBA
 * @param {string} hex - Color en formato hexadecimal
 * @param {number} alpha - Valor de transparencia (0-1)
 * @returns {string} Color en formato RGBA
 */
function hexToRgba(hex, alpha) {
    const r = parseInt(hex.slice(1, 3), 16);
    const g = parseInt(hex.slice(3, 5), 16);
    const b = parseInt(hex.slice(5, 7), 16);
    
    return `rgba(${r}, ${g}, ${b}, ${alpha})`;
}

/**
 * Maneja el evento de cambio de especialidad
 */
function handleEspecialidadChange() {
    const especialidadId = document.getElementById('especialidad').value;
    const medicoSelect = document.getElementById('medico');
    
    // Reiniciar el select de médicos
    if (especialidadId === '0') {
        medicoSelect.innerHTML = '<option value="0">Todos</option>';
        medicoSelect.disabled = true;
    } else {
        medicoSelect.disabled = false;
        cargarMedicos(especialidadId);
    }
}

/**
 * Configura los event listeners para los filtros
 */
function configurarEventListeners() {
    // Event listener para el botón de filtrar
    const btnFiltrar = document.getElementById('btn-filtrar');
    if (btnFiltrar) {
        btnFiltrar.addEventListener('click', cargarTendencias);
    }
    
    // Event listener para el cambio de especialidad
    const especialidadSelect = document.getElementById('especialidad');
    if (especialidadSelect) {
        especialidadSelect.addEventListener('change', handleEspecialidadChange);
    }
    
    // Event listener para el cambio de fechas
    const fechaInicio = document.getElementById('fecha_inicio');
    const fechaFin = document.getElementById('fecha_fin');
    
    if (fechaInicio) {
        fechaInicio.addEventListener('change', () => {
            // Actualizar fecha mínima para fecha fin
            if (fechaFin) {
                fechaFin.min = fechaInicio.value;
            }
        });
    }
}

/**
 * Inicializa la página cuando el DOM está cargado
 */
document.addEventListener('DOMContentLoaded', function() {
    console.log('Inicializando página de tendencias de citas...');
    
    try {
        // Configurar event listeners
        configurarEventListeners();
        
        // Establecer fechas por defecto si no están definidas
        const fechaInicio = document.getElementById('fecha_inicio');
        const fechaFin = document.getElementById('fecha_fin');
        
        if (fechaInicio && !fechaInicio.value) {
            // Establecer fecha de inicio como primer día del mes actual
            const hoy = new Date();
            const primerDia = new Date(hoy.getFullYear(), hoy.getMonth(), 1);
            fechaInicio.value = primerDia.toISOString().split('T')[0];
        }
        
        if (fechaFin && !fechaFin.value) {
            // Establecer fecha fin como día actual
            const hoy = new Date();
            fechaFin.value = hoy.toISOString().split('T')[0];
        }
        
        // Cargar datos iniciales
        setTimeout(() => {
            console.log('Cargando datos iniciales de tendencias...');
            cargarTendencias();
        }, 500); // Pequeño retraso para asegurar que todo esté inicializado
    } catch (error) {
        console.error('Error durante la inicialización:', error);
    }
});
