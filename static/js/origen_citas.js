// Gráficos y variables globales
let distribucionChart;
let estadosChart;
let tendenciaChart;
let datosOriginales = null;

// Definición de colores para gráficos
const colores = {
    paciente: '#4A6FDC',     // Azul
    derivacion: '#FF8C00',    // Naranja
    seguimiento: '#2DCE89',   // Verde
    admision: '#F5365C'       // Rojo
};

// Función para obtener cookies (para CSRF token)
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

// Configurar AJAX para incluir el token CSRF en todas las solicitudes
$(document).ready(function() {
    const csrftoken = getCookie('csrftoken');
    
    // Configurar AJAX para usar el token en todas las solicitudes
    $.ajaxSetup({
        beforeSend: function(xhr, settings) {
            if (!this.crossDomain) {
                xhr.setRequestHeader("X-CSRFToken", csrftoken);
            }
        }
    });
});

$(document).ready(function() {
    console.log('DOM cargado, inicializando componentes...');
    
    // Inicializar DateRangePicker
    if ($.fn.daterangepicker) {
        $('#rangoFechas').daterangepicker({
            locale: {
                format: 'YYYY-MM-DD',
                separator: ' - ',
                applyLabel: 'Aplicar',
                cancelLabel: 'Cancelar',
                fromLabel: 'Desde',
                toLabel: 'Hasta',
                customRangeLabel: 'Personalizado',
                weekLabel: 'S',
                daysOfWeek: ['Do', 'Lu', 'Ma', 'Mi', 'Ju', 'Vi', 'Sa'],
                monthNames: ['Enero', 'Febrero', 'Marzo', 'Abril', 'Mayo', 'Junio', 'Julio', 'Agosto', 'Septiembre', 'Octubre', 'Noviembre', 'Diciembre'],
                firstDay: 1
            },
            startDate: $('#fecha_inicio').val(),
            endDate: $('#fecha_fin').val(),
            opens: 'left'
        }, function(start, end, label) {
            // Actualizar campos ocultos con fechas seleccionadas
            $('#fecha_inicio').val(start.format('YYYY-MM-DD'));
            $('#fecha_fin').val(end.format('YYYY-MM-DD'));
            console.log('Fechas actualizadas:', $('#fecha_inicio').val(), $('#fecha_fin').val());
        });
        console.log('DateRangePicker inicializado');
    } else {
        console.error('DateRangePicker no está disponible');
    }
    
    // Evento de cambio en el selector de especialidad
    $('#especialidad').change(function() {
        const especialidadId = $(this).val();
        console.log('Especialidad seleccionada:', especialidadId);
        
        if (especialidadId) {
            // Habilitar y cargar médicos para esta especialidad
            cargarMedicosPorEspecialidad(especialidadId);
        } else {
            // Si no hay especialidad seleccionada, deshabilitar selector de médicos
            $('#medico').prop('disabled', true).html('<option value="">Seleccione un médico</option>');
        }
    });
    
    // Manejar envío del formulario
    $('#filtrosForm').submit(function(e) {
        e.preventDefault();
        console.log('Formulario enviado, cargando datos...');
        cargarDatos();
    });
    
    // Cargar datos iniciales
    console.log('Cargando datos iniciales...');
    cargarDatos();
});

document.addEventListener('DOMContentLoaded', function() {
    // Inicializar gráficos vacíos
    inicializarGraficos();
});

// Función para cargar médicos según especialidad seleccionada
function cargarMedicosPorEspecialidad(especialidadId) {
    // Mostrar indicador de carga
    $('#medico').html('<option value="">Cargando médicos...</option>');
    $('#medico').prop('disabled', true);
    
    console.log('Cargando médicos para especialidad ID:', especialidadId);
    
    // Realizar petición AJAX para obtener médicos por especialidad
    $.ajax({
        url: '/api/medicos-por-especialidad/',
        method: 'GET',
        data: { especialidad_id: especialidadId },
        dataType: 'json',
        success: function(data) {
            // Limpiar y agregar opción por defecto
            $('#medico').empty();
            $('#medico').append('<option value="">Todos los médicos</option>');
            
            console.log('Respuesta completa:', data);
            
            try {
                // Acceder a la propiedad 'medicos' del objeto de respuesta
                if (data && data.medicos && Array.isArray(data.medicos)) {
                    // Iterar sobre el array de médicos
                    $.each(data.medicos, function(index, medico) {
                        if (medico && medico.id && medico.nombre) {
                            $('#medico').append(`<option value="${medico.id}">${medico.nombre}</option>`);
                        }
                    });
                    
                    console.log(`Médicos cargados: ${data.medicos.length}`);
                } else {
                    console.error('Formato inesperado o no hay médicos:', data);
                }
            } catch (error) {
                console.error('Error al procesar datos de médicos:', error);
            }
            
            // Habilitar selector
            $('#medico').prop('disabled', false);
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error('Error al cargar médicos:');
            console.error('Status:', textStatus);
            console.error('Error:', errorThrown);
            
            // En caso de error, mostrar mensaje y deshabilitar
            $('#medico').html('<option value="">Error al cargar médicos</option>');
            $('#medico').prop('disabled', true);
        }
    });
}

// Función para cargar datos desde la API
function cargarDatos() {
    // Mostrar overlay de carga
    $('#loadingOverlay').css('display', 'flex');
    
    // Obtener fechas - verificar que estamos obteniendo los valores correctamente
    // Los campos ocultos tienen id fecha_inicio y fecha_fin
    const fechaInicio = $('#fecha_inicio').val();
    const fechaFin = $('#fecha_fin').val();
    
    console.log('Fechas seleccionadas:', fechaInicio, fechaFin);
    
    // Verificar que tenemos fechas válidas
    if (!fechaInicio || !fechaFin) {
        console.error('Fechas no válidas');
        alert('Por favor seleccione un rango de fechas válido');
        $('#loadingOverlay').css('display', 'none');
        return;
    }
    
    // Obtener filtros adicionales
    const especialidad = $('#especialidad').val();
    const medico = $('#medico').val();
    
    console.log('Filtros adicionales:', { especialidad, medico });
    
    // Construir URL correcta para la API
    const url = '/api/citas/origen/';
    
    // Parámetros para la petición
    const params = {
        fecha_inicio: fechaInicio,
        fecha_fin: fechaFin
    };
    
    // Añadir parámetros opcionales solo si tienen valor
    if (especialidad && especialidad !== '') {
        params.especialidad = especialidad;
    }
    
    if (medico && medico !== '') {
        params.medico = medico;
    }
    
    console.log('URL de API:', url);
    console.log('Parámetros:', params);
    
    // Utilizar el token CSRF configurado globalmente en $.ajaxSetup
    
    // Realizar petición AJAX
    $.ajax({
        url: url,
        method: 'GET',
        data: params,
        dataType: 'json',
        cache: false,
        beforeSend: function(xhr) {
            console.log('Iniciando petición a:', url, 'con parámetros:', params);
            // El token CSRF ya se agrega mediante $.ajaxSetup global
        },
        success: function(data) {
            console.log('Datos recibidos correctamente:', data);
            // Verificar si los datos son válidos
            if (data && typeof data === 'object') {
                // Guardar datos originales
                datosOriginales = data;
                
                try {
                    // Actualizar UI
                    actualizarTarjetas(data);
                    actualizarGraficos(data);
                    actualizarTablaEspecialidades(data);
                    generarInterpretacion(data);
                } catch (error) {
                    console.error('Error al actualizar la interfaz:', error);
                    alert('Ocurrió un error al procesar los datos. Por favor, contacte al administrador.');
                }
            } else {
                console.error('Los datos recibidos no tienen el formato esperado:', data);
                alert('Los datos recibidos no tienen el formato esperado. Por favor, contacte al administrador.');
            }
            
            // Ocultar overlay de carga
            $('#loadingOverlay').css('display', 'none');
        },
        error: function(jqXHR, textStatus, errorThrown) {
            console.error('Error al cargar datos:');
            console.error('Status:', textStatus);
            console.error('Error:', errorThrown);
            
            try {
                // Intentar parsear el mensaje de error del servidor
                const errorResponse = jqXHR.responseJSON || JSON.parse(jqXHR.responseText);
                console.error('Mensaje del servidor:', errorResponse);
                
                if (errorResponse && errorResponse.error) {
                    alert(`Error del servidor: ${errorResponse.error}`);
                } else if (errorResponse && errorResponse.mensaje) {
                    alert(`Error del servidor: ${errorResponse.mensaje}`);
                } else {
                    alert(`Error al cargar datos: ${textStatus}. Por favor, verifique la consola para más detalles.`);
                }
            } catch (e) {
                console.error('No se pudo parsear la respuesta de error:', e);
                alert(`Error al cargar datos: ${textStatus}. Por favor, verifique la consola para más detalles.`);
            }
            
            // Ocultar overlay de carga
            $('#loadingOverlay').css('display', 'none');
        }
    });
}

// Función para inicializar gráficos vacíos
function inicializarGraficos() {
    // Inicializar gráfico de distribución por origen
    const ctxDistribucion = document.getElementById('distribucionOrigenChart').getContext('2d');
    distribucionChart = new Chart(ctxDistribucion, {
        type: 'doughnut',
        data: {
            labels: ['Paciente', 'Derivación', 'Seguimiento', 'Admisión'],
            datasets: [{
                data: [0, 0, 0, 0],
                backgroundColor: [
                    colores.paciente,
                    colores.derivacion,
                    colores.seguimiento,
                    colores.admision
                ],
                borderWidth: 2
            }]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'right',
                    labels: {
                        boxWidth: 12
                    }
                },
                tooltip: {
                    callbacks: {
                        label: function(context) {
                            const label = context.label || '';
                            const value = context.parsed || 0;
                            const dataset = context.dataset;
                            const total = dataset.data.reduce((acc, data) => acc + data, 0);
                            const percentage = total > 0 ? Math.round((value / total) * 100) : 0;
                            return `${label}: ${value} (${percentage}%)`;
                        }
                    }
                }
            }
        }
    });
    
    // Inicializar gráfico de estados por origen
    const ctxEstados = document.getElementById('estadosOrigenChart').getContext('2d');
    estadosChart = new Chart(ctxEstados, {
        type: 'bar',
        data: {
            labels: ['Pendiente', 'Confirmada', 'Atendida', 'Cancelada'],
            datasets: [
                {
                    label: 'Paciente',
                    data: [0, 0, 0, 0],
                    backgroundColor: colores.paciente,
                    borderColor: colores.paciente,
                    borderWidth: 1
                },
                {
                    label: 'Derivación',
                    data: [0, 0, 0, 0],
                    backgroundColor: colores.derivacion,
                    borderColor: colores.derivacion,
                    borderWidth: 1
                },
                {
                    label: 'Seguimiento',
                    data: [0, 0, 0, 0],
                    backgroundColor: colores.seguimiento,
                    borderColor: colores.seguimiento,
                    borderWidth: 1
                },
                {
                    label: 'Admisión',
                    data: [0, 0, 0, 0],
                    backgroundColor: colores.admision,
                    borderColor: colores.admision,
                    borderWidth: 1
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    stacked: false,
                },
                y: {
                    stacked: false,
                    beginAtZero: true
                }
            }
        }
    });
    
    // Inicializar gráfico de tendencia por origen
    const ctxTendencia = document.getElementById('tendenciaOrigenChart').getContext('2d');
    tendenciaChart = new Chart(ctxTendencia, {
        type: 'line',
        data: {
            labels: [],
            datasets: [
                {
                    label: 'Paciente',
                    data: [],
                    backgroundColor: colores.paciente,
                    borderColor: colores.paciente,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Derivación',
                    data: [],
                    backgroundColor: colores.derivacion,
                    borderColor: colores.derivacion,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Seguimiento',
                    data: [],
                    backgroundColor: colores.seguimiento,
                    borderColor: colores.seguimiento,
                    tension: 0.3,
                    fill: false
                },
                {
                    label: 'Admisión',
                    data: [],
                    backgroundColor: colores.admision,
                    borderColor: colores.admision,
                    tension: 0.3,
                    fill: false
                }
            ]
        },
        options: {
            responsive: true,
            maintainAspectRatio: false,
            plugins: {
                legend: {
                    position: 'top',
                },
                tooltip: {
                    mode: 'index',
                    intersect: false
                }
            },
            scales: {
                x: {
                    title: {
                        display: true,
                        text: 'Fecha'
                    }
                },
                y: {
                    beginAtZero: true,
                    title: {
                        display: true,
                        text: 'Cantidad de citas'
                    }
                }
            }
        }
    });
}

// Función para actualizar tarjetas con estadísticas
function actualizarTarjetas(data) {
    const total = data.total_general;
    const paciente = data.distribucion_origen.paciente;
    const derivacion = data.distribucion_origen.derivacion;
    const seguimiento = data.distribucion_origen.seguimiento;
    const admision = data.distribucion_origen.admision;
    
    // Actualizar números
    $('#totalCitas').text(total);
    $('#citasPaciente').text(paciente);
    $('#citasDerivacion').text(derivacion);
    $('#citasSeguimiento').text(seguimiento);
    $('#citasAdmision').text(admision);
    
    // Calcular porcentajes
    const porcPaciente = total > 0 ? ((paciente / total) * 100).toFixed(1) : 0;
    const porcDerivacion = total > 0 ? ((derivacion / total) * 100).toFixed(1) : 0;
    const porcSeguimiento = total > 0 ? ((seguimiento / total) * 100).toFixed(1) : 0;
    const porcAdmision = total > 0 ? ((admision / total) * 100).toFixed(1) : 0;
    
    // Actualizar porcentajes en la UI
    $('#porcPaciente span').text(`${porcPaciente}%`);
    $('#porcDerivacion span').text(`${porcDerivacion}%`);
    $('#porcSeguimiento span').text(`${porcSeguimiento}%`);
    $('#porcAdmision span').text(`${porcAdmision}%`);
}

// Función para actualizar gráficos
function actualizarGraficos(data) {
    // Datos para el gráfico de distribución
    distribucionChart.data.datasets[0].data = [
        data.distribucion_origen.paciente,
        data.distribucion_origen.derivacion,
        data.distribucion_origen.seguimiento,
        data.distribucion_origen.admision
    ];
    distribucionChart.update();
    
    // Datos para el gráfico de estados
    const estados = ['pendiente', 'confirmada', 'atendida', 'cancelada'];
    
    estadosChart.data.datasets[0].data = estados.map(estado => data.estados.paciente[estado] || 0);
    estadosChart.data.datasets[1].data = estados.map(estado => data.estados.derivacion[estado] || 0);
    estadosChart.data.datasets[2].data = estados.map(estado => data.estados.seguimiento[estado] || 0);
    estadosChart.data.datasets[3].data = estados.map(estado => data.estados.admision[estado] || 0);
    estadosChart.update();
    
    // Datos para el gráfico de tendencia
    // Procesar fechas y ordenarlas
    const fechasPaciente = Object.keys(data.dias_semana.paciente).sort();
    const fechasDerivacion = Object.keys(data.dias_semana.derivacion).sort();
    const fechasSeguimiento = Object.keys(data.dias_semana.seguimiento).sort();
    const fechasAdmision = Object.keys(data.dias_semana.admision).sort();
    
    // Combinar todas las fechas y eliminar duplicados
    const todasFechas = [...new Set([...fechasPaciente, ...fechasDerivacion, ...fechasSeguimiento, ...fechasAdmision])].sort();
    
    // Formatear fechas para mostrar en formato DD/MM
    const fechasFormateadas = todasFechas.map(fecha => {
        const partes = fecha.split('-');
        return `${partes[2]}/${partes[1]}`;
    });
    
    // Preparar datos para cada origen
    const datosPaciente = todasFechas.map(fecha => data.dias_semana.paciente[fecha] || 0);
    const datosDerivacion = todasFechas.map(fecha => data.dias_semana.derivacion[fecha] || 0);
    const datosSeguimiento = todasFechas.map(fecha => data.dias_semana.seguimiento[fecha] || 0);
    const datosAdmision = todasFechas.map(fecha => data.dias_semana.admision[fecha] || 0);
    
    // Actualizar gráfico de tendencia
    tendenciaChart.data.labels = fechasFormateadas;
    tendenciaChart.data.datasets[0].data = datosPaciente;
    tendenciaChart.data.datasets[1].data = datosDerivacion;
    tendenciaChart.data.datasets[2].data = datosSeguimiento;
    tendenciaChart.data.datasets[3].data = datosAdmision;
    tendenciaChart.update();
}

// Función para actualizar tabla de especialidades
function actualizarTablaEspecialidades(data) {
    // Obtener todas las especialidades únicas
    const especialidadesPaciente = data.especialidades.paciente;
    const especialidadesDerivacion = data.especialidades.derivacion;
    const especialidadesSeguimiento = data.especialidades.seguimiento;
    const especialidadesAdmision = data.especialidades.admision;
    
    // Crear un mapa para almacenar los datos por especialidad
    const mapaEspecialidades = new Map();
    
    // Función para agregar datos al mapa
    const agregarDatos = (especialidades, tipo) => {
        especialidades.forEach(esp => {
            const nombre = esp.medico__especialidad__nombre;
            if (!nombre) return;
            
            if (!mapaEspecialidades.has(nombre)) {
                mapaEspecialidades.set(nombre, {
                    paciente: 0,
                    derivacion: 0,
                    seguimiento: 0,
                    admision: 0,
                    total: 0
                });
            }
            
            const datos = mapaEspecialidades.get(nombre);
            datos[tipo] = esp.total;
            datos.total += esp.total;
        });
    };
    
    // Agregar datos de cada origen
    agregarDatos(especialidadesPaciente, 'paciente');
    agregarDatos(especialidadesDerivacion, 'derivacion');
    agregarDatos(especialidadesSeguimiento, 'seguimiento');
    agregarDatos(especialidadesAdmision, 'admision');
    
    // Convertir mapa a array para ordenar
    const especialidadesArray = Array.from(mapaEspecialidades.entries())
        .map(([nombre, datos]) => ({ nombre, ...datos }))
        .sort((a, b) => b.total - a.total);
    
    // Generar HTML para la tabla
    let html = '';
    
    if (especialidadesArray.length === 0) {
        html = '<tr><td colspan="6" class="text-center">No hay datos disponibles</td></tr>';
    } else {
        especialidadesArray.forEach(esp => {
            html += `
                <tr>
                    <td>
                        <div class="d-flex px-2 py-1">
                            <div class="d-flex flex-column justify-content-center">
                                <h6 class="mb-0 text-sm">${esp.nombre}</h6>
                            </div>
                        </div>
                    </td>
                    <td>
                        <span class="badge-paciente origen-badge">${esp.paciente}</span>
                    </td>
                    <td>
                        <span class="badge-derivacion origen-badge">${esp.derivacion}</span>
                    </td>
                    <td>
                        <span class="badge-seguimiento origen-badge">${esp.seguimiento}</span>
                    </td>
                    <td>
                        <span class="badge-admision origen-badge">${esp.admision}</span>
                    </td>
                    <td>
                        <span class="text-secondary text-xs font-weight-bold">${esp.total}</span>
                    </td>
                </tr>
            `;
        });
    }
    
    // Actualizar la tabla
    $('#tablaEspecialidades').html(html);
}

// Función para generar interpretación de los datos
function generarInterpretacion(data) {
    console.log('Generando interpretación de datos...');
    
    const total = data.total_general;
    const paciente = data.distribucion_origen.paciente;
    const derivacion = data.distribucion_origen.derivacion;
    const seguimiento = data.distribucion_origen.seguimiento;
    const admision = data.distribucion_origen.admision;
    
    // Calcular porcentajes
    const porcPaciente = total > 0 ? ((paciente / total) * 100).toFixed(1) : 0;
    const porcDerivacion = total > 0 ? ((derivacion / total) * 100).toFixed(1) : 0;
    const porcSeguimiento = total > 0 ? ((seguimiento / total) * 100).toFixed(1) : 0;
    const porcAdmision = total > 0 ? ((admision / total) * 100).toFixed(1) : 0;
    
    // Ordenar orígenes por cantidad
    const origenes = [
        { nombre: 'paciente', valor: paciente, porcentaje: porcPaciente },
        { nombre: 'derivación', valor: derivacion, porcentaje: porcDerivacion },
        { nombre: 'seguimiento', valor: seguimiento, porcentaje: porcSeguimiento },
        { nombre: 'admisión', valor: admision, porcentaje: porcAdmision }
    ].sort((a, b) => b.valor - a.valor);
    
    // Analizar estados de citas (pendiente, confirmada, atendida, cancelada)
    const estados = ['pendiente', 'confirmada', 'atendida', 'cancelada'];
    const totalEstados = {};
    const porcEstados = {};
    
    // Inicializar contadores
    estados.forEach(estado => {
        totalEstados[estado] = 0;
    });
    
    // Sumar estados por cada origen
    for (const origen of ['paciente', 'derivacion', 'seguimiento', 'admision']) {
        for (const estado of estados) {
            if (data.estados[origen] && data.estados[origen][estado] !== undefined) {
                totalEstados[estado] += data.estados[origen][estado];
            }
        }
    }
    
    // Calcular porcentajes de estados
    estados.forEach(estado => {
        porcEstados[estado] = total > 0 ? ((totalEstados[estado] / total) * 100).toFixed(1) : 0;
    });
    
    // Generar texto de interpretación
    let interpretacion = '';
    
    if (total === 0) {
        interpretacion = 'No hay datos disponibles para el período seleccionado.';
    } else {
        // Resumen general
        interpretacion += `<p>En el periodo seleccionado se han registrado <strong>${total} citas</strong> en total.</p>`;
        
        // Distribución por origen
        interpretacion += `<p>La mayoría de las citas (${origenes[0].porcentaje}%) provienen de <strong>${origenes[0].nombre}</strong>`;        
        if (origenes.length > 1) {
            interpretacion += `, seguidas por <strong>${origenes[1].nombre}</strong> (${origenes[1].porcentaje}%)`;
        }
        interpretacion += `.</p>`;
        
        // Distribución detallada
        interpretacion += `<p>Distribución por origen: 
            <span class="badge bg-primary">${porcPaciente}% Paciente</span> 
            <span class="badge bg-warning">${porcDerivacion}% Derivación</span> 
            <span class="badge bg-success">${porcSeguimiento}% Seguimiento</span> 
            <span class="badge bg-danger">${porcAdmision}% Admisión</span>
        </p>`;
        
        // Estados de citas
        interpretacion += `<p>Respecto al estado de las citas: 
            <span class="badge bg-success">${porcEstados.atendida}% Atendidas</span> 
            <span class="badge bg-primary">${porcEstados.pendiente}% Pendientes</span> 
            <span class="badge bg-info">${porcEstados.confirmada}% Confirmadas</span> 
            <span class="badge bg-danger">${porcEstados.cancelada}% Canceladas</span>
        </p>`;
        
        // Obtener especialidades principales
        if (data.especialidades && Object.keys(data.especialidades).length > 0) {
            const especialidadesPorOrigen = data.especialidades;
            let especialidadesPrincipales = [];
            
            for (const origen in especialidadesPorOrigen) {
                if (especialidadesPorOrigen[origen] && especialidadesPorOrigen[origen].length > 0) {
                    // Tomar las top 2 especialidades de cada origen
                    const top = especialidadesPorOrigen[origen]
                        .filter(esp => esp.medico__especialidad__nombre) // Filtrar valores nulos
                        .sort((a, b) => b.total - a.total)
                        .slice(0, 2);
                        
                    especialidadesPrincipales = [...especialidadesPrincipales, ...top];
                }
            }
            
            // Eliminar duplicados y ordenar por total
            const especialidadesMap = new Map();
            especialidadesPrincipales.forEach(esp => {
                const nombre = esp.medico__especialidad__nombre;
                if (!especialidadesMap.has(nombre)) {
                    especialidadesMap.set(nombre, esp.total);
                } else {
                    especialidadesMap.set(nombre, especialidadesMap.get(nombre) + esp.total);
                }
            });
            
            const topEspecialidades = Array.from(especialidadesMap)
                .sort((a, b) => b[1] - a[1])
                .slice(0, 3);
            
            if (topEspecialidades.length > 0) {
                interpretacion += `<p>Las especialidades más solicitadas son: `;
                topEspecialidades.forEach((esp, index) => {
                    interpretacion += `<strong>${esp[0]}</strong>`;
                    if (index < topEspecialidades.length - 1) {
                        interpretacion += index === topEspecialidades.length - 2 ? ' y ' : ', ';
                    }
                });
                interpretacion += `.</p>`;
            }
        }
    }
    
    // Actualizar el contenedor de interpretación
    $('#interpretacion').html(`
        <div class="alert alert-info">
            <h4>Análisis de Datos</h4>
            ${interpretacion}
        </div>
    `);
    console.log('Interpretación generada');
}
