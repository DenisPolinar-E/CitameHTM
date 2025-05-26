$(document).ready(function() {
    // Configurar fecha mínima como hoy
    var today = new Date();
    var dd = String(today.getDate()).padStart(2, '0');
    var mm = String(today.getMonth() + 1).padStart(2, '0');
    var yyyy = today.getFullYear();
    today = yyyy + '-' + mm + '-' + dd;
    $('#fecha_cita').attr('min', today);
    
    // Alertas de prueba para verificar funcionamiento
    alert('¡Script de derivación cargado! jQuery versión: ' + $.fn.jquery);
    
    // Inicialmente mostrar la sección de agendamiento para facilitar pruebas
    $('#seccion-agendamiento').show();
    
    // Evento de cambio en el selector de especialidades
    $('#especialidad').change(function() {
        var especialidadId = $(this).val();
        console.log('Especialidad seleccionada:', especialidadId);
        
        if (especialidadId) {
            // Mostrar alerta de prueba
            alert('Seleccionaste la especialidad ID: ' + especialidadId);
            
            // Mostrar sección de agendamiento
            $('#seccion-agendamiento').show();
            
            // Limpiar y preparar el selector de médicos
            $('#medico_especialista')
                .html('<option value="">Cargando médicos...</option>')
                .prop('disabled', true);
            
            $('#horario_cita')
                .html('<option value="">Seleccione un médico primero</option>')
                .prop('disabled', true);
            
            // Cargar médicos para esta especialidad
            $.ajax({
                url: '/api/derivacion/medicos-por-especialidad/' + especialidadId + '/',
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    alert('Médicos encontrados: ' + (data ? data.length : 0));
                    
                    var options = '<option value="">Seleccione un médico</option>';
                    
                    if (data && data.length > 0) {
                        for (var i = 0; i < data.length; i++) {
                            var medico = data[i];
                            options += '<option value="' + medico.id + '">' + 
                                     medico.nombres + ' ' + medico.apellidos + ' - CMP: ' + 
                                     (medico.cmp || 'N/A') + '</option>';
                        }
                    } else {
                        options = '<option value="">No hay médicos disponibles</option>';
                    }
                    
                    $('#medico_especialista').html(options).prop('disabled', false);
                },
                error: function(xhr, status, error) {
                    alert('Error al cargar médicos: ' + error);
                    console.error('Error AJAX:', status, error);
                    console.error('Respuesta:', xhr.responseText);
                    $('#medico_especialista')
                        .html('<option value="">Error al cargar médicos</option>')
                        .prop('disabled', false);
                }
            });
        } else {
            // Ocultar sección si no hay especialidad seleccionada
            $('#seccion-agendamiento').hide();
            $('#medico_especialista').html('<option value="">Seleccione una especialidad primero</option>');
        }
    });
    
    // Cuando se selecciona un médico, habilitar la selección de fecha
    $('#medico_especialista').change(function() {
        var medicoId = $(this).val();
        
        if (medicoId) {
            $('#fecha_cita').prop('disabled', false);
        } else {
            $('#fecha_cita').prop('disabled', true).val('');
            $('#horario_cita')
                .html('<option value="">Seleccione un médico primero</option>')
                .prop('disabled', true);
        }
    });
    
    // Cuando cambia la fecha, cargar horarios disponibles
    $('#fecha_cita').change(function() {
        var medicoId = $('#medico_especialista').val();
        var fecha = $(this).val();
        
        if (medicoId && fecha) {
            $('#horario_cita').html('<option value="">Cargando horarios...</option>').prop('disabled', true);
            
            // Cargar horarios disponibles
            $.ajax({
                url: '/api/derivacion/horarios-disponibles/' + medicoId + '/' + fecha + '/',
                type: 'GET',
                dataType: 'json',
                success: function(data) {
                    var options = '<option value="">Seleccione un horario</option>';
                    
                    if (data && data.length > 0) {
                        for (var i = 0; i < data.length; i++) {
                            var horario = data[i];
                            options += '<option value="' + horario.id + '" data-consultorio="' + 
                                    horario.consultorio + '">' + horario.hora_inicio + ' - ' + 
                                    horario.hora_fin + '</option>';
                        }
                    } else {
                        options = '<option value="">No hay horarios disponibles</option>';
                    }
                    
                    $('#horario_cita').html(options).prop('disabled', false);
                },
                error: function(xhr, status, error) {
                    alert('Error al cargar horarios: ' + error);
                    $('#horario_cita').html('<option value="">Error al cargar horarios</option>');
                }
            });
        } else {
            $('#horario_cita').html('<option value="">Seleccione médico y fecha</option>').prop('disabled', true);
        }
    });
    
    // Cuando selecciona horario, mostrar consultorio
    $('#horario_cita').change(function() {
        var consultorio = $('option:selected', this).data('consultorio');
        $('#consultorio').val(consultorio || '');
    });
    
    // Validar formulario antes de enviar
    $('#derivacionForm').submit(function(e) {
        var especialidad = $('#especialidad').val();
        var motivo = $('#motivo_derivacion').val().trim();
        var medico = $('#medico_especialista').val();
        var fecha = $('#fecha_cita').val();
        var horario = $('#horario_cita').val();
        
        if (!especialidad || !motivo) {
            e.preventDefault();
            alert('Por favor complete todos los campos obligatorios.');
            return false;
        }
        
        // Si se seleccionó médico, validar que también tenga fecha y horario
        if (medico && (!fecha || !horario)) {
            e.preventDefault();
            alert('Si selecciona un médico, debe también seleccionar fecha y horario para la cita.');
            return false;
        }
        
        return true;
    });
});
