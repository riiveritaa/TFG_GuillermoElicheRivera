document.addEventListener('DOMContentLoaded', () => {

    if (typeof ChartDataLabels !== 'undefined') { Chart.register(ChartDataLabels); }
    Chart.defaults.color = '#95A5A6';
    Chart.defaults.font.family = 'Poppins';

    let globalCuentas = [];

    const cargarDatos = async () => {
        try {
            const respuesta = await fetch('/api/datos_dashboard');
            if (!respuesta.ok) { window.location.href = '/'; return; }
            const data = await respuesta.json();
            
            globalCuentas = data.cuentas;

            pintarDatosUsuario(data);
            pintarMovimientos(data.movimientos);
            pintarGraficoBarras(data.grafico_barras);
            pintarGraficoRosca(data.cuentas); 
            actualizarDesplegablesCuentas(data.cuentas); 
            rellenarGestionCuentas(data.cuentas); 
            
        } catch (error) { console.error("Error al cargar datos:", error); }
    };

    const pintarDatosUsuario = (data) => {
        document.getElementById('saludo_usuario').innerText = `Hola, ${data.usuario.nombre}`;
        document.getElementById('titulo_historial').innerText = `Historial de Movimientos - ${data.mes_actual} ${data.anio_actual}`;
        document.getElementById('pct_fijo').value = data.usuario.pct_fijo;
        document.getElementById('pct_ocio').value = data.usuario.pct_ocio;
        document.getElementById('pct_ahorro').value = data.usuario.pct_ahorro;
    };

    const pintarMovimientos = (movimientos) => {
        const contenedor = document.getElementById('contenedor_movimientos');
        contenedor.innerHTML = '';
        if (movimientos.length === 0) {
            contenedor.innerHTML = '<p class="empty-state-text">No hay movimientos registrados este mes.</p>';
            return;
        }
        movimientos.forEach(mov => {
            const esIngreso = mov.tipo === 'ingreso';
            contenedor.innerHTML += `
                <div class="history-item">
                    <div class="item-left">
                        <div class="icon-circle ${esIngreso ? 'bg-green' : 'bg-red'}">
                            <i class='bx ${esIngreso ? 'bx-trending-up' : 'bx-trending-down'}'></i>
                        </div>
                        <div class="item-details">
                            <span class="item-concept">${mov.concepto}</span>
                            <span class="item-category">${mov.categoria.toUpperCase()} | ${mov.fecha}</span>
                        </div>
                    </div>
                    <div class="item-actions">
                        <span class="item-amount ${esIngreso ? 'amount-positive' : 'amount-negative'}">${esIngreso ? '+' : '-'}${mov.cantidad.toFixed(2)} €</span>
                        
                        <button class="btn-action edit btnEditarMovimiento" 
                                data-id="${mov.id}" 
                                data-tipo="${mov.tipo}" 
                                data-concepto="${mov.concepto}" 
                                data-categoria="${mov.categoria}" 
                                data-cantidad="${mov.cantidad}" 
                                data-cuenta="${mov.cuenta_id}" 
                                data-fecha="${mov.fecha}" 
                                title="Editar transacción">
                            <i class='bx bx-edit-alt'></i>
                        </button>
                        
                        <button class="btn-action delete btnEliminarMovimiento" data-id="${mov.id}" title="Borrar transacción"><i class='bx bx-trash'></i></button>
                    </div>
                </div>
            `;
        });
        
        // EVENTO: ELIMINAR MOVIMIENTO
        document.querySelectorAll('.btnEliminarMovimiento').forEach(btn => {
            btn.addEventListener('click', async (e) => {
                if(confirm("¿Seguro que deseas eliminar esta transacción? Se revertirá el saldo de la cuenta.")) {
                    const res = await fetch(`/api/eliminar_movimiento/${e.currentTarget.dataset.id}`, { method: 'DELETE' });
                    if(res.ok) location.reload();
                }
            });
        });

        // EVENTO: EDITAR MOVIMIENTO (ABRIR MODAL)
        document.querySelectorAll('.btnEditarMovimiento').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const dataset = e.currentTarget.dataset;
                
                // Rellenar datos en el modal de edición
                document.getElementById('edit_movimiento_id').value = dataset.id;
                document.getElementById('edit_tipo_movimiento').value = dataset.tipo;
                document.getElementById('edit_concepto').value = dataset.concepto;
                document.getElementById('edit_cantidad').value = dataset.cantidad;
                document.getElementById('edit_fecha').value = dataset.fecha;
                
                // Mostrar/Ocultar y setear categoría
                if (dataset.tipo === 'ingreso') {
                    document.getElementById('edit_grupoCategoria').style.display = 'none';
                    document.getElementById('edit_categoria').value = 'ingreso';
                } else {
                    document.getElementById('edit_grupoCategoria').style.display = 'block';
                    document.getElementById('edit_categoria').value = dataset.categoria;
                }
                
                // Rellenar desplegable de cuentas y seleccionar la correcta
                const selectEditCuenta = document.getElementById('edit_cuenta_id');
                selectEditCuenta.innerHTML = '';
                globalCuentas.forEach(c => {
                    selectEditCuenta.innerHTML += `<option value="${c.id}">${c.nombre} (${c.saldo.toFixed(2)}€)</option>`;
                });
                selectEditCuenta.value = dataset.cuenta;
                
                document.getElementById('modalEditarMovimiento').style.display = 'flex';
            });
        });
    };

    const actualizarDesplegablesCuentas = (cuentas) => {
        const select = document.getElementById('cuenta_id');
        select.innerHTML = '';
        cuentas.forEach(c => {
            select.innerHTML += `<option value="${c.id}">${c.nombre} (${c.saldo.toFixed(2)}€)</option>`;
        });
    };

    const rellenarGestionCuentas = (cuentas) => {
        const contenedorGestion = document.getElementById('contenedor_gestion_cuentas');
        contenedorGestion.innerHTML = '';
        if (cuentas.length === 0) { contenedorGestion.innerHTML = '<p class="empty-state-text">No tienes cuentas añadidas.</p>'; return; }

        cuentas.forEach(c => {
            contenedorGestion.innerHTML += `
                <div class="cuenta-item">
                    <div><span class="modal-cuenta-nombre">${c.nombre}</span><span class="modal-cuenta-saldo">${c.saldo.toFixed(2)} €</span></div>
                    <div class="item-actions-small">
                        <button class="btn-icon delete btnEliminarCuenta" data-id="${c.id}" data-nombre="${c.nombre}" data-saldo="${c.saldo}" title="Eliminar cuenta">
                            <i class='bx bx-trash'></i>
                        </button>
                    </div>
                </div>`;
        });

        document.querySelectorAll('.btnEliminarCuenta').forEach(btn => {
            btn.addEventListener('click', (e) => {
                const idBorrar = Number(e.currentTarget.dataset.id);
                const nombreBorrar = e.currentTarget.dataset.nombre;
                const saldoBorrar = parseFloat(e.currentTarget.dataset.saldo);

                if (globalCuentas.length <= 1) { alert("No puedes eliminar tu única cuenta. Debes tener al menos una."); return; }

                if (saldoBorrar > 0) abrirModalTraspaso(idBorrar, nombreBorrar, saldoBorrar);
                else {
                    if(confirm(`¿Estás seguro de eliminar la cuenta "${nombreBorrar}"?`)) {
                        ejecutarBorradoDirecto(idBorrar);
                    }
                }
            });
        });
    };

    const abrirModalTraspaso = (idBorrar, nombreBorrar, saldoBorrar) => {
        document.getElementById('id_cuenta_borrar_oculto').value = idBorrar;
        document.getElementById('nombre_cuenta_a_borrar').innerText = nombreBorrar;
        document.getElementById('saldo_a_transferir').innerText = saldoBorrar.toFixed(2);

        const selectDestino = document.getElementById('cuenta_destino_id');
        selectDestino.innerHTML = '';
        const cuentasDestinoPosibles = globalCuentas.filter(c => c.id !== idBorrar);
        cuentasDestinoPosibles.forEach(c => selectDestino.innerHTML += `<option value="${c.id}">${c.nombre} (${c.saldo.toFixed(2)}€)</option>`);
        document.getElementById('modalTransferirSaldo').style.display = 'flex';
    };

    const ejecutarBorradoDirecto = async (idBorrar) => {
        try {
            const res = await fetch('/api/eliminar_cuenta', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ cuenta_id_borrar: idBorrar }) });
            if(res.ok) location.reload();
            else { const err = await res.json(); alert(err.error || "Error al borrar"); }
        } catch (error) { console.error(error); }
    };

    const pintarGraficoBarras = (datosBarras) => {
        const ctx = document.getElementById('graficoDistribucion');
        new Chart(ctx, {
            type: 'bar',
            data: { 
                labels: ['Fijos', 'Ocio', 'Ahorro'], 
                datasets: [
                    { label: 'Presupuestado', data: datosBarras.presupuestado, backgroundColor: 'rgba(149, 165, 166, 0.3)', borderRadius: 4 }, 
                    { label: 'Gastado', data: datosBarras.gastado, backgroundColor: ['#E74C3C', '#F39C12', '#2ECC71'], borderRadius: 4 }
                ] 
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { legend: { position: 'top', labels: { color: '#95A5A6', font: {family: 'Poppins', size: 11} } }, datalabels: { display: true, color: '#fff', align: 'top', font: { weight: 'bold', size: 10, family: 'Poppins' }, formatter: (v) => v > 0 ? Math.round(v) + '€' : '' } },
                scales: { y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' }, ticks: { color: '#95A5A6', font: {family: 'Poppins', size: 10} } }, x: { grid: { display: false }, ticks: { color: '#95A5A6', font: {family: 'Poppins', size: 10} } } }
            }
        });
    };

    const pintarGraficoRosca = (cuentas) => {
        const ctx = document.getElementById('graficoRosca');
        if(!ctx) return;
        new Chart(ctx, {
            type: 'doughnut',
            data: { labels: cuentas.map(c => c.nombre), datasets: [{ data: cuentas.map(c => c.saldo), backgroundColor: ['#3498DB', '#9B59B6', '#E67E22', '#1ABC9C', '#F1C40F', '#E74C3C'], borderWidth: 2, borderColor: '#1A222F' }] },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '70%',
                plugins: {
                    legend: { position: 'right', labels: { color: '#95A5A6', padding: 15, font: {family: 'Poppins', size: 11} } },
                    tooltip: { callbacks: { label: function(context) { return ' ' + (context.parsed !== null ? context.parsed.toFixed(2) + ' €' : ''); } } },
                    datalabels: { display: true, color: '#fff', font: {weight: 'bold', family: 'Poppins', size: 10}, formatter: (value, ctx) => { let sum = 0; ctx.chart.data.datasets[0].data.forEach((val, i) => { if (ctx.chart.getDataVisibility(i)) sum += val; }); return sum>0 ? (value * 100 / sum).toFixed(0) + '%' : ''; } }
                }
            },
            plugins: [{ id: 'textCenter', beforeDraw: (chart) => { const ctx = chart.ctx; ctx.restore(); let sum = 0; chart.data.datasets[0].data.forEach((val, i) => { if (chart.getDataVisibility(i)) sum += val; }); const meta = chart.getDatasetMeta(0); if(!meta || !meta.data || !meta.data.length) return; ctx.font = "bold 1.1rem Poppins"; ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle"; ctx.fillText(sum.toFixed(2)+" €", meta.data[0].x, meta.data[0].y); ctx.save(); } }]
        });
    };

    const obtenerFechaHoy = () => new Date().toISOString().split('T')[0];

    const openModal = (idB, idM) => document.getElementById(idB)?.addEventListener('click', () => document.getElementById(idM).style.display = 'flex');
    openModal('btnIngreso', 'modalMovimiento'); openModal('btnGasto', 'modalMovimiento'); openModal('btnConfig', 'modalConfig'); openModal('btnAñadirCuenta', 'modalCuenta'); openModal('btnGestionCuentas', 'modalGestionCuentas');

    document.getElementById('btnIngreso')?.addEventListener('click', () => {
        document.getElementById('modalTitulo').innerText = 'Nuevo Ingreso'; document.getElementById('tipo_movimiento').value = 'ingreso';
        document.getElementById('grupoCategoria').style.display = 'none'; document.getElementById('categoria').value = 'ingreso';
        document.getElementById('fecha').value = obtenerFechaHoy();
    });
    document.getElementById('btnGasto')?.addEventListener('click', () => {
        document.getElementById('modalTitulo').innerText = 'Nuevo Gasto'; document.getElementById('tipo_movimiento').value = 'gasto';
        document.getElementById('grupoCategoria').style.display = 'block'; document.getElementById('categoria').value = 'fijo';
        document.getElementById('fecha').value = obtenerFechaHoy();
    });

    document.querySelectorAll('.btn-cancelar').forEach(btn => btn.addEventListener('click', () => document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none')));
    document.getElementById('btnCancelarTraspaso')?.addEventListener('click', (e) => { e.stopPropagation(); document.getElementById('modalTransferirSaldo').style.display = 'none'; });

    const enviarForm = (formId, url) => {
        const form = document.getElementById(formId);
        if(!form) return;
        form.addEventListener('submit', async (e) => {
            e.preventDefault(); // Evita que la página se recargue
            const formData = {};
        
            // Extraemos todos los inputs del formulario dinámicamente
            form.querySelectorAll('input, select').forEach(i => { 
                if(i.id) formData[i.id] = i.value; 
            });
        
            // Validación especial en el cliente para el presupuesto
            if (formId === 'formConfig') {
                const suma = Number(formData.pct_fijo) + Number(formData.pct_ocio) + Number(formData.pct_ahorro);
                if (suma > 100) { 
                    alert(`La suma no puede ser mayor al 100%.`); return; 
                }
            }

            // Petición POST asíncrona al servidor Flask
            const res = await fetch(url, { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(formData) 
            });
        
            if(res.ok) location.reload();
            else { 
                const err = await res.json(); 
                alert(err.error || "Error procesando formulario"); 
            }
        });
    };

    enviarForm('formMovimiento', '/api/crear_movimiento');
    enviarForm('formEditarMovimiento', '/api/editar_movimiento'); // REGISTRO DEL FORM DE EDICIÓN
    enviarForm('formCuenta', '/api/crear_cuenta');
    enviarForm('formConfig', '/api/ajustar_presupuesto');

    document.getElementById('formTransferirEliminar')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const idBorrar = document.getElementById('id_cuenta_borrar_oculto').value;
        const idDestino = document.getElementById('cuenta_destino_id').value;
        if(!idDestino) { alert("Selecciona cuenta destino"); return; }
        try {
            const res = await fetch('/api/eliminar_cuenta', { method: 'POST', headers: {'Content-Type': 'application/json'}, body: JSON.stringify({ cuenta_id_borrar: idBorrar, cuenta_id_destino: idDestino }) });
            if(res.ok) location.reload();
            else { const err = await res.json(); alert(err.error || "Error al traspasar y borrar"); }
        } catch (error) { console.error(error); }
    });

    cargarDatos();
});