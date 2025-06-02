/**
 * tasas_asistencia.js
 * Script para la página de Tasas de Asistencia
 *
 * Versión: 1.2.0 - Actualizado: 01/06/2025
 * 
 * Este script maneja:
 * - La carga dinámica de médicos según la especialidad seleccionada
 * - La carga y visualización de tasas de asistencia, inasistencia, cancelación y recuperación
 * - La visualización de gráficos y tablas con la evolución de las tasas
 */

// Mensaje de diagnóstico - Esto aparecerá en la consola cuando el script se cargue
console.log('=== SCRIPT DE TASAS DE ASISTENCIA CARGADO ===');

// Utilizar jQuery para garantizar que el DOM esté completamente cargado
$(document).ready(function() {
    console.log('DOM completamente cargado con jQuery!');
    console.log('Versión de jQuery:', $.fn.jquery);
    
    // Configurar event listeners
    setupEventListeners();
    
    // Inicializar la página
    inicializarFechas();
    
    // Cargar médicos para la especialidad inicial si está seleccionada
    const especialidadId = $('#especialidad').val();
    console.log('Especialidad inicial:', especialidadId);
    if (especialidadId && especialidadId !== '0') {
        cargarMedicos(especialidadId);
    } else {
        // Si no hay especialidad seleccionada, asegurarse de que el selector de médicos tenga la opción "Todos"
        $('#medico').html('<option value="0">Todos</option>');
    }
    
    // Cargar datos iniciales
    cargarDatos();
});

/**
 * Configura los event listeners para los elementos de la interfaz
 */
function setupEventListeners() {
    // Event listener para el cambio de especialidad
    const $especialidadSelect = $('#especialidad');
    if ($especialidadSelect.length) {
        $especialidadSelect.on('change', function() {
            handleEspecialidadChange();
        });
    }
    
    // Event listener para el botón de filtro
    const $btnFiltrar = $('#btn-aplicar-filtro');
    if ($btnFiltrar.length) {
        $btnFiltrar.on('click', function() {
            cargarDatos();
        });
    }
    
    // Event listeners para las fechas
    const $fechaInicio = $('#fecha_inicio');
    const $fechaFin = $('#fecha_fin');
    
    if ($fechaInicio.length && $fechaFin.length) {
        $fechaInicio.on('change', function() {
            // Establecer la fecha mínima para fecha fin
            $fechaFin.attr('min', $fechaInicio.val());
        });
    }
}

// Gráfico global para poder actualizarlo
let graficoEvolucion;

/**
 * Inicializa los campos de fecha con valores predeterminados
 */
function inicializarFechas() {
    // Establecer fecha fin como hoy
    const hoy = new Date();
    const fechaFin = hoy.toISOString().split('T')[0];
    document.getElementById('fecha_fin').value = fechaFin;

    // Establecer fecha inicio como 3 meses atrás
    hoy.setMonth(hoy.getMonth() - 3);
    const fechaInicio = hoy.toISOString().split('T')[0];
    document.getElementById('fecha_inicio').value = fechaInicio;
}

/**
 * Inicializa los eventos de la página
 * NOTA: Esta función ya no se usa directamente ya que los eventos se configuran en $(document).ready()
 */
function inicializarEventos() {
    console.log('Método inicializarEventos() descontinuado - Los eventos ahora se configuran en $(document).ready()');
}

/**
 * Obtiene los filtros actuales del formulario
 */
function obtenerFiltros() {
    return {
        fecha_inicio: document.getElementById('fecha_inicio').value,
        fecha_fin: document.getElementById('fecha_fin').value,
        especialidad_id: document.getElementById('especialidad').value,
        medico_id: document.getElementById('medico').value
    };
}

/**
 * Maneja el evento de cambio de especialidad
 */
function handleEspecialidadChange() {
    const $especialidadSelect = $('#especialidad');
    const $medicoSelect = $('#medico');
    const especialidadId = $especialidadSelect.val();
    
    console.log('Especialidad cambiada a:', especialidadId);
    
    // Reiniciar el select de médicos
    if (!especialidadId || especialidadId === '0') {
        $medicoSelect.html('<option value="0">Todos</option>');
        // No desactivamos el select para permitir que el usuario pueda seleccionar 'Todos'
        // pero podríamos hacerlo si fuera necesario: $medicoSelect.prop('disabled', true);
    } else {
        // Llamamos a la función que carga los médicos
        cargarMedicos(especialidadId);
    }
}

/**
 * Carga los médicos según la especialidad seleccionada
 * Esta función utiliza jQuery para simplificar las operaciones AJAX
 * @param {string} especialidadId - ID de la especialidad
 */
function cargarMedicos(especialidadId) {
    console.log('=== CARGANDO MÉDICOS ===');
    console.log('Especialidad seleccionada:', especialidadId);
    
    // Obtener el selector de médicos
    const $medicoSelect = $('#medico');
    
    if ($medicoSelect.length === 0) {
        console.error('ERROR: El selector de médicos no se encontró en el DOM');
        return;
    }
    
    // Si no hay especialidad seleccionada, solo mostrar la opción "Todos"
    if (!especialidadId || especialidadId === '0') {
        $medicoSelect.html('<option value="0">Todos</option>');
        return;
    }
    
    // Mostrar estado de carga
    $medicoSelect.html('<option value="0">Cargando...</option>');
    $medicoSelect.prop('disabled', true);
    
    // URL de la API
    const url = `/api/medicos-por-especialidad/?especialidad_id=${especialidadId}`;
    console.log('Llamando a API:', url);
    
    // Realizar la petición AJAX con jQuery
    $.ajax({
        url: url,
        type: 'GET',
        dataType: 'json',
        success: function(data) {
            console.log('Datos recibidos:', data);
            
            // Reiniciar el selector con la opción 'Todos'
            $medicoSelect.html('<option value="0">Todos</option>');
            
            // Agregar los médicos si existen
            if (data.medicos && data.medicos.length > 0) {
                $.each(data.medicos, function(i, medico) {
                    $medicoSelect.append(`<option value="${medico.id}">${medico.nombre}</option>`);
                });
                console.log(`Se agregaron ${data.medicos.length} médicos al selector`);
            } else {
                console.log('No se encontraron médicos para esta especialidad');
            }
            
            // Habilitar el selector
            $medicoSelect.prop('disabled', false);
        },
        error: function(xhr, status, error) {
            console.error('Error al cargar médicos:', error);
            console.error('Estado HTTP:', status);
            console.error('Respuesta:', xhr.responseText);
            
            // En caso de error, mostrar mensaje de error
            $medicoSelect.html('<option value="0">Error al cargar médicos</option>');
            $medicoSelect.prop('disabled', false);
        }
    });
}

/**
 * Carga los datos de tasas de asistencia
 */
function cargarDatos() {
    const filtros = obtenerFiltros();
    
    // Validar fechas
    if (!validarFechas(filtros)) {
        return;
    }

    // Construir la URL con los parámetros de filtro
    const params = new URLSearchParams();
    for (const key in filtros) {
        if (filtros[key] && filtros[key] !== '0') {
            params.append(key, filtros[key]);
        }
    }
    
    // Mostrar indicador de carga
    document.getElementById('tasa-asistencia').innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    document.getElementById('tasa-inasistencia').innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    document.getElementById('tasa-cancelacion').innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    document.getElementById('tasa-recuperacion').innerHTML = '<i class="fas fa-spinner fa-spin"></i>';
    
    console.log('Parámetros de consulta:', params.toString());
    
    // Hacer la petición a la API
    fetch(`/api/tasas-asistencia/?${params.toString()}`)
        .then(response => {
            console.log('Respuesta API status:', response.status);
            if (!response.ok) {
                throw new Error('Error en la respuesta del servidor');
            }
            return response.json();
        })
        .then(data => {
            console.log('Datos recibidos de la API:', data);
            console.log('Status de la respuesta:', data.status);
            console.log('Tasas:', data.tasas);
            console.log('Recuperación:', data.recuperacion);
            
            // Verificar estructura esperada
            if (!data.recuperacion || typeof data.recuperacion.inasistencias_totales === 'undefined') {
                console.error('Error: Estructura de datos incompleta', data);
                throw new Error('La respuesta no contiene los datos esperados');
            }
            
            actualizarMetricas(data);
            actualizarGrafico(data);
            actualizarTablaRecuperacion(data);
        })
        .catch(error => {
            console.error('Error al cargar datos:', error);
            // Mostrar mensaje de error
            alert('Error al cargar los datos. Por favor intente nuevamente.');
            // Restablecer valores por defecto
            document.getElementById('tasa-asistencia').textContent = '0%';
            document.getElementById('tasa-inasistencia').textContent = '0%';
            document.getElementById('tasa-cancelacion').textContent = '0%';
            document.getElementById('tasa-recuperacion').textContent = '0%';
        });
}

/**
 * Valida que las fechas sean correctas
 */
function validarFechas(filtros) {
    if (!filtros.fecha_inicio || !filtros.fecha_fin) {
        alert('Por favor seleccione ambas fechas');
        return false;
    }
    
    const fechaInicio = new Date(filtros.fecha_inicio);
    const fechaFin = new Date(filtros.fecha_fin);
    
    if (fechaInicio > fechaFin) {
        alert('La fecha de inicio no puede ser posterior a la fecha fin');
        return false;
    }
    
    return true;
}

/**
 * Actualiza las métricas principales
 */
function actualizarMetricas(data) {
    // Formatear porcentajes
    const formatearPorcentaje = (valor) => `${valor.toFixed(1)}%`;
    
    // Actualizar valores en el DOM
    document.getElementById('tasa-asistencia').textContent = formatearPorcentaje(data.tasas.asistencia);
    document.getElementById('tasa-inasistencia').textContent = formatearPorcentaje(data.tasas.inasistencia);
    document.getElementById('tasa-cancelacion').textContent = formatearPorcentaje(data.tasas.cancelacion);
    
    // Tasa de recuperación con clase de color según valor
    const tasaRecuperacion = document.getElementById('tasa-recuperacion');
    tasaRecuperacion.textContent = formatearPorcentaje(data.tasas.recuperacion);
    
    // Quitar clases anteriores
    tasaRecuperacion.classList.remove('recovery-high', 'recovery-medium', 'recovery-low');
    
    // Agregar clase según el valor
    if (data.tasas.recuperacion >= 70) {
        tasaRecuperacion.classList.add('recovery-high');
    } else if (data.tasas.recuperacion >= 40) {
        tasaRecuperacion.classList.add('recovery-medium');
    } else {
        tasaRecuperacion.classList.add('recovery-low');
    }
}

/**
 * Actualiza la tabla de recuperación
 */
function actualizarTablaRecuperacion(data) {
    console.log('Actualizando tabla de recuperación con datos:', data.recuperacion);
    
    // Verificar si tenemos los datos necesarios
    if (!data.recuperacion || typeof data.recuperacion.inasistencias_totales === 'undefined' || 
        typeof data.recuperacion.inasistencias_recuperadas === 'undefined') {
        console.error('Error: Datos de recuperación inválidos o incompletos', data.recuperacion);
        return;
    }
    
    // Obtener los datos de recuperación
    const inasistencias = data.recuperacion.inasistencias_totales;
    const recuperadas = data.recuperacion.inasistencias_recuperadas;
    
    console.log(`Inasistencias totales: ${inasistencias}, Recuperadas: ${recuperadas}`);
    
    // Calcular valores derivados
    const noRecuperadas = inasistencias - recuperadas;
    const porcentajeRecuperadas = inasistencias > 0 ? (recuperadas / inasistencias) * 100 : 0;
    const porcentajeNoRecuperadas = inasistencias > 0 ? (noRecuperadas / inasistencias) * 100 : 0;
    
    console.log(`No recuperadas: ${noRecuperadas}, % Recuperadas: ${porcentajeRecuperadas.toFixed(1)}%, % No recuperadas: ${porcentajeNoRecuperadas.toFixed(1)}%`);
    
    // Verificar si los elementos esenciales de la tabla existen antes de actualizarlos
    const elementosEsenciales = [
        'inasistencias-total', 'inasistencias-recuperadas', 'inasistencias-no-recuperadas',
        'porcentaje-recuperadas', 'porcentaje-no-recuperadas'
    ];
    
    let elementosFaltantes = [];
    
    elementosEsenciales.forEach(id => {
        const elemento = document.getElementById(id);
        if (!elemento) {
            elementosFaltantes.push(id);
        }
    });
    
    if (elementosFaltantes.length > 0) {
        console.error('Error: Elementos esenciales no encontrados en el DOM:', elementosFaltantes);
        return; // Solo detenemos la función si faltan elementos esenciales
    }
    
    // Actualizar los elementos en el DOM
    document.getElementById('inasistencias-total').textContent = inasistencias;
    document.getElementById('inasistencias-recuperadas').textContent = recuperadas;
    document.getElementById('inasistencias-no-recuperadas').textContent = noRecuperadas;
    document.getElementById('porcentaje-recuperadas').textContent = `${porcentajeRecuperadas.toFixed(1)}%`;
    document.getElementById('porcentaje-no-recuperadas').textContent = `${porcentajeNoRecuperadas.toFixed(1)}%`;
    
    // Crear o actualizar la interpretación
    let interpretacionContainer = document.getElementById('interpretacion-container');
    let interpretacionTexto;
    
    // Si no existe el contenedor, lo creamos dinámicamente
    if (!interpretacionContainer) {
        console.log('Creando contenedor de interpretación dinámicamente...');
        
        // Obtener la tabla de recuperación
        const tablaRecuperacion = document.getElementById('tabla-recuperacion');
        if (!tablaRecuperacion) {
            console.error('No se pudo encontrar la tabla de recuperación');
            return;
        }
        
        // Buscar el contenedor padre de la tabla (div.table-responsive)
        const tableResponsive = tablaRecuperacion.closest('.table-responsive');
        if (!tableResponsive) {
            console.error('No se pudo encontrar el contenedor de la tabla');
            return;
        }
        
        // Crear el contenedor de interpretación
        interpretacionContainer = document.createElement('div');
        interpretacionContainer.id = 'interpretacion-container';
        interpretacionContainer.className = 'mt-3 p-3 rounded';
        
        // Crear el título
        const titulo = document.createElement('h6');
        titulo.className = 'font-weight-bold';
        titulo.textContent = 'Interpretación:';
        
        // Crear el texto
        interpretacionTexto = document.createElement('p');
        interpretacionTexto.id = 'interpretacion-texto';
        interpretacionTexto.className = 'mb-0 font-italic';
        
        // Armar el contenedor
        interpretacionContainer.appendChild(titulo);
        interpretacionContainer.appendChild(interpretacionTexto);
        
        // Insertar el contenedor después de la tabla
        tableResponsive.insertAdjacentElement('afterend', interpretacionContainer);
    } else {
        interpretacionTexto = document.getElementById('interpretacion-texto');
        
        // Si existe el contenedor pero no el texto, creamos el texto
        if (!interpretacionTexto) {
            interpretacionTexto = document.createElement('p');
            interpretacionTexto.id = 'interpretacion-texto';
            interpretacionTexto.className = 'mb-0 font-italic';
            
            // Buscar si hay un título, si no crearlo
            let titulo = interpretacionContainer.querySelector('h6');
            if (!titulo) {
                titulo = document.createElement('h6');
                titulo.className = 'font-weight-bold';
                titulo.textContent = 'Interpretación:';
                interpretacionContainer.appendChild(titulo);
            }
            
            interpretacionContainer.appendChild(interpretacionTexto);
        }
    }
    
    // Generar interpretación de los datos
    const textoGenerado = generarInterpretacion(inasistencias, recuperadas, porcentajeRecuperadas);
    interpretacionTexto.innerHTML = textoGenerado;
    
    // Cambiar el color del contenedor de interpretación según el rendimiento
    interpretacionContainer.className = interpretacionContainer.className.replace(/bg-\w+/g, '');
    interpretacionContainer.classList.add('mt-3', 'p-3', 'rounded'); // Asegurar clases básicas
    
    if (inasistencias === 0) {
        interpretacionContainer.classList.add('bg-light');
    } else if (porcentajeRecuperadas >= 70) {
        interpretacionContainer.classList.add('bg-success', 'text-white');
    } else if (porcentajeRecuperadas >= 40) {
        interpretacionContainer.classList.add('bg-warning');
    } else {
        interpretacionContainer.classList.add('bg-danger', 'text-white');
    }
    
    console.log('Interpretación actualizada con éxito');
    
    console.log('Tabla de recuperación actualizada exitosamente');
}

/**
 * Genera una interpretación de los datos de recuperación
 */
function generarInterpretacion(inasistencias, recuperadas, porcentajeRecuperadas) {
    // Si no hay inasistencias
    if (inasistencias === 0) {
        return `<strong>No hay inasistencias registradas</strong> en el período seleccionado. 
               Esto puede indicar un excelente nivel de asistencia o que aún no hay citas con estado "confirmada" 
               donde el paciente no asistió.`;
    }
    
    // Si hay inasistencias pero ninguna recuperada
    if (recuperadas === 0) {
        return `<strong>Ninguna de las ${inasistencias} inasistencias ha sido recuperada</strong>. 
               Esto representa una oportunidad para mejorar el seguimiento a los pacientes 
               que no asisten a sus citas programadas.`;
    }
    
    // Evaluar el rendimiento según el porcentaje de recuperación
    let calificacion = '';
    let recomendacion = '';
    
    if (porcentajeRecuperadas >= 80) {
        calificacion = 'Excelente';
        recomendacion = 'Mantenga las estrategias actuales de seguimiento a pacientes.';
    } else if (porcentajeRecuperadas >= 60) {
        calificacion = 'Muy bueno';
        recomendacion = 'Considere compartir las mejores prácticas con otras áreas del hospital.';
    } else if (porcentajeRecuperadas >= 40) {
        calificacion = 'Aceptable';
        recomendacion = 'Hay espacio para mejorar el seguimiento a pacientes que no asisten.';
    } else if (porcentajeRecuperadas >= 20) {
        calificacion = 'Bajo';
        recomendacion = 'Considere implementar un protocolo más efectivo de seguimiento a inasistencias.';
    } else {
        calificacion = 'Crítico';
        recomendacion = 'Se requiere atención inmediata. Implemente un plan de acción para mejorar la recuperación.';
    }
    
    return `<strong>${calificacion}:</strong> Se han recuperado ${recuperadas} de ${inasistencias} inasistencias (${porcentajeRecuperadas.toFixed(1)}%). 
            ${recomendacion}`;
}

/**
 * Actualiza el gráfico de evolución de tasas
 */
function actualizarGrafico(data) {
    console.log('Intentando actualizar gráfico...');
    
    // Verificar que Chart.js esté disponible
    if (typeof Chart === 'undefined') {
        console.error('ERROR CRÍTICO: Chart.js no está disponible. No se puede crear el gráfico.');
        alert('Error al cargar la biblioteca de gráficos. Por favor recargue la página o contacte al administrador.');
        return;
    }
    
    // Verificar que el canvas exista
    const canvas = document.getElementById('graficoEvolucion');
    if (!canvas) {
        console.error('ERROR: No se encontró el elemento canvas con id "graficoEvolucion"');
        return;
    }
    
    // Obtener el contexto 2D
    try {
        const ctx = canvas.getContext('2d');
        
        // Destruir gráfico anterior si existe
        if (graficoEvolucion) {
            console.log('Destruyendo gráfico anterior...');
            graficoEvolucion.destroy();
        }
        
        console.log('Datos para el gráfico:', data.evolucion);
        
        // Crear nuevo gráfico con manejo de errores
        try {
            graficoEvolucion = new Chart(ctx, {
                type: 'line',
                data: {
                    labels: data.evolucion.etiquetas,
                    datasets: [
                        {
                            label: 'Tasa de Asistencia',
                            data: data.evolucion.asistencia,
                            borderColor: '#4e73df',
                            backgroundColor: 'rgba(78, 115, 223, 0.1)',
                            borderWidth: 2,
                            pointBackgroundColor: '#4e73df',
                            tension: 0.3
                        },
                        {
                            label: 'Tasa de Recuperación',
                            data: data.evolucion.recuperacion,
                            borderColor: '#1cc88a',
                            backgroundColor: 'rgba(28, 200, 138, 0.1)',
                            borderWidth: 2,
                            pointBackgroundColor: '#1cc88a',
                            tension: 0.3
                        }
                    ]
                },
                options: {
                    responsive: true,
                    maintainAspectRatio: false,
                    scales: {
                        y: {
                            beginAtZero: true,
                            max: 100,
                            ticks: {
                                callback: function(value) {
                                    return value + '%';
                                }
                            }
                        }
                    },
                    plugins: {
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.dataset.label}: ${context.raw.toFixed(1)}%`;
                                }
                            }
                        }
                    }
                }
            });
            console.log('Gráfico creado exitosamente');
        } catch (chartError) {
            console.error('Error al crear el gráfico:', chartError);
            alert('Error al generar el gráfico. Por favor intente nuevamente más tarde.');
        }
    } catch (ctxError) {
        console.error('Error al obtener el contexto 2D del canvas:', ctxError);
    }
}
