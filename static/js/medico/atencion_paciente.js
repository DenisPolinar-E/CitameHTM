// Manejo de la receta médica
document.addEventListener('DOMContentLoaded', function() {
    // Referencias a elementos del DOM
    const prescripcionRadios = document.querySelectorAll('input[name="prescribir_receta"]');
    const bloqueReceta = document.getElementById('bloque_receta_medica');
    const buscadorMedicamento = document.getElementById('buscador_medicamento');
    const resultadosMedicamentos = document.getElementById('resultados_medicamentos');
    const medicamentosSeleccionados = document.getElementById('medicamentos_seleccionados');
    const noMedicamentosAlert = document.getElementById('no_medicamentos_alert');
    const contadorMedicamentos = document.getElementById('contador_medicamentos');
    let timeoutId;

    // Mostrar/ocultar bloque de receta médica
    prescripcionRadios.forEach(radio => {
        radio.addEventListener('change', function() {
            bloqueReceta.style.display = this.value === 'si' ? 'block' : 'none';
            if (this.value === 'no') {
                // Limpiar medicamentos al desactivar
                medicamentosSeleccionados.innerHTML = '';
                actualizarContadorMedicamentos();
                noMedicamentosAlert.style.display = 'block';
            }
        });
    });

    // Búsqueda de medicamentos con debounce
    buscadorMedicamento.addEventListener('input', function() {
        clearTimeout(timeoutId);
        const query = this.value.trim();
        
        if (query.length < 2) {
            resultadosMedicamentos.style.display = 'none';
            return;
        }

        timeoutId = setTimeout(() => {
            buscarMedicamentos(query);
        }, 300);
    });

    // Función para buscar medicamentos
    function buscarMedicamentos(query) {
        fetch(`/api/medicamentos/buscar/?q=${encodeURIComponent(query)}`)
            .then(response => response.json())
            .then(data => {
                resultadosMedicamentos.innerHTML = '';
                resultadosMedicamentos.style.display = data.length > 0 ? 'block' : 'none';

                data.forEach(med => {
                    const item = document.createElement('a');
                    item.href = '#';
                    item.className = 'list-group-item list-group-item-action';
                    
                    const stockClass = med.stock > 20 ? 'success' : (med.stock > 5 ? 'warning' : 'danger');
                    
                    item.innerHTML = `
                        <div class="d-flex justify-content-between align-items-center">
                            <div>
                                <h6 class="mb-1">${med.nombre_comercial}</h6>
                                <small class="text-muted">${med.nombre_generico}</small>
                            </div>
                            <span class="badge bg-${stockClass}">${med.stock} en stock</span>
                        </div>
                    `;

                    item.addEventListener('click', (e) => {
                        e.preventDefault();
                        agregarMedicamento(med);
                        resultadosMedicamentos.style.display = 'none';
                        buscadorMedicamento.value = '';
                    });

                    resultadosMedicamentos.appendChild(item);
                });
            })
            .catch(error => {
                console.error('Error al buscar medicamentos:', error);
                resultadosMedicamentos.innerHTML = `
                    <div class="list-group-item text-danger">
                        <i class="fas fa-exclamation-circle me-2"></i>
                        Error al buscar medicamentos
                    </div>
                `;
                resultadosMedicamentos.style.display = 'block';
            });
    }

    // Función para agregar un medicamento a la receta
    function agregarMedicamento(medicamento) {
        const medicamentoId = `med_${medicamento.id}`;
        
        // Evitar duplicados
        if (document.getElementById(medicamentoId)) {
            alert('Este medicamento ya está en la receta');
            return;
        }

        const card = document.createElement('div');
        card.id = medicamentoId;
        card.className = 'card mb-3 border-primary medicamento-card';
        card.innerHTML = `
            <div class="card-header bg-primary text-white d-flex justify-content-between align-items-center">
                <h5 class="mb-0">${medicamento.nombre_comercial}</h5>
                <button type="button" class="btn btn-sm btn-close btn-close-white" aria-label="Eliminar"></button>
            </div>
            <div class="card-body">
                <input type="hidden" name="medicamento_ids[]" value="${medicamento.id}">
                
                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label">Nombre genérico</label>
                        <input type="text" class="form-control" value="${medicamento.nombre_generico}" readonly>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Presentación</label>
                        <input type="text" class="form-control" value="${medicamento.presentacion}" readonly>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="col-md-4">
                        <label class="form-label">Dosis por toma</label>
                        <div class="input-group">
                            <input type="number" class="form-control dosis" name="dosis[]" min="0.5" step="0.5" required>
                            <span class="input-group-text">unidad(es)</span>
                        </div>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">Frecuencia</label>
                        <select class="form-select frecuencia" name="frecuencia[]" required>
                            <option value="">Seleccione...</option>
                            <option value="4">Cada 4 horas</option>
                            <option value="6">Cada 6 horas</option>
                            <option value="8">Cada 8 horas</option>
                            <option value="12">Cada 12 horas</option>
                            <option value="24">Cada 24 horas</option>
                        </select>
                    </div>
                    <div class="col-md-4">
                        <label class="form-label">Duración (días)</label>
                        <input type="number" class="form-control duracion" name="duracion[]" min="1" required>
                    </div>
                </div>

                <div class="row mb-3">
                    <div class="col-md-6">
                        <label class="form-label">Cantidad total</label>
                        <div class="input-group">
                            <input type="number" class="form-control cantidad-total" name="cantidad[]" readonly>
                            <span class="input-group-text">unidades</span>
                        </div>
                        <small class="text-muted">Se calcula automáticamente</small>
                    </div>
                    <div class="col-md-6">
                        <label class="form-label">Indicaciones</label>
                        <textarea class="form-control" name="indicaciones[]" rows="2" required 
                                placeholder="Ej: Tomar con agua, después de las comidas..."></textarea>
                    </div>
                </div>

                <div class="stock-warning alert alert-warning" style="display: none;">
                    <i class="fas fa-exclamation-triangle me-2"></i>
                    La cantidad requerida excede el stock disponible (${medicamento.stock} unidades)
                </div>
            </div>
        `;

        // Agregar eventos a los campos
        const dosis = card.querySelector('.dosis');
        const frecuencia = card.querySelector('.frecuencia');
        const duracion = card.querySelector('.duracion');
        const cantidadTotal = card.querySelector('.cantidad-total');
        const stockWarning = card.querySelector('.stock-warning');

        function calcularCantidadTotal() {
            if (dosis.value && frecuencia.value && duracion.value) {
                const dosisNum = parseFloat(dosis.value);
                const frecuenciaNum = parseInt(frecuencia.value);
                const duracionNum = parseInt(duracion.value);
                
                const tomasAlDia = 24 / frecuenciaNum;
                const cantidadCalculada = Math.ceil(dosisNum * tomasAlDia * duracionNum);
                
                cantidadTotal.value = cantidadCalculada;
                
                // Verificar stock
                stockWarning.style.display = cantidadCalculada > medicamento.stock ? 'block' : 'none';
            }
        }

        [dosis, frecuencia, duracion].forEach(campo => {
            campo.addEventListener('input', calcularCantidadTotal);
        });

        // Evento para eliminar el medicamento
        card.querySelector('.btn-close').addEventListener('click', () => {
            card.remove();
            actualizarContadorMedicamentos();
            if (medicamentosSeleccionados.children.length === 0) {
                noMedicamentosAlert.style.display = 'block';
            }
        });

        medicamentosSeleccionados.appendChild(card);
        noMedicamentosAlert.style.display = 'none';
        actualizarContadorMedicamentos();
    }

    // Función para actualizar el contador de medicamentos
    function actualizarContadorMedicamentos() {
        const cantidad = medicamentosSeleccionados.children.length;
        contadorMedicamentos.textContent = `${cantidad} medicamento${cantidad !== 1 ? 's' : ''}`;
    }

    // Cerrar resultados al hacer clic fuera
    document.addEventListener('click', function(e) {
        if (!resultadosMedicamentos.contains(e.target) && e.target !== buscadorMedicamento) {
            resultadosMedicamentos.style.display = 'none';
        }
    });

    // Validación del formulario
    document.getElementById('atencion-form').addEventListener('submit', function(e) {
        const prescribirReceta = document.querySelector('input[name="prescribir_receta"]:checked').value;
        
        if (prescribirReceta === 'si') {
            const medicamentos = medicamentosSeleccionados.children.length;
            if (medicamentos === 0) {
                e.preventDefault();
                alert('Debe agregar al menos un medicamento a la receta');
                return;
            }

            // Verificar que todos los medicamentos tengan sus campos completos
            const medicamentosCards = document.querySelectorAll('.medicamento-card');
            for (const card of medicamentosCards) {
                const campos = card.querySelectorAll('input[required], select[required], textarea[required]');
                for (const campo of campos) {
                    if (!campo.value) {
                        e.preventDefault();
                        alert('Por favor complete todos los campos requeridos en los medicamentos');
                        campo.focus();
                        return;
                    }
                }

                // Verificar stock
                const stockWarning = card.querySelector('.stock-warning');
                if (stockWarning.style.display === 'block') {
                    e.preventDefault();
                    alert('Uno o más medicamentos exceden el stock disponible');
                    return;
                }
            }
        }
    });
}); 