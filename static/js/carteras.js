document.addEventListener('DOMContentLoaded', () => {

    // =========================================================================
    // UTILIDADES Y MODALES
    // =========================================================================

    /**
     * Vincula un botón a la apertura de un modal específico de forma segura.
     */
    const safeOpenModal = (btnId, modalId) => {
        const btn = document.getElementById(btnId);
        const modal = document.getElementById(modalId);
        if(btn && modal) {
            btn.addEventListener('click', () => modal.style.display = 'flex');
        }
    };

    safeOpenModal('btnCrearCartera', 'modalCrearCartera'); 
    safeOpenModal('btnAñadirPosicion', 'modalAgregarPosicion');
    safeOpenModal('btnTraspasoBroker', 'modalTraspasoBroker');

    const cerrarModales = () => {
        document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
    };
    document.querySelectorAll('.btn-cancelar').forEach(btn => btn.addEventListener('click', cerrarModales));

    // =========================================================================
    // LÓGICA DE COMPORTAMIENTO INTERACTIVO (FRONTEND)
    // =========================================================================

    // Lógica dinámica para el Modal de Añadir Activo:
    // Muestra u oculta campos (ej. Peso Objetivo) dependiendo de si es cartera o individual
    const selCartera = document.getElementById('posicion_cartera_id');
    const bloqueCompra = document.getElementById('bloque_compra_directa');
    const bloquePeso = document.getElementById('bloque_peso_objetivo');
    
    if (selCartera && bloqueCompra) {
        selCartera.addEventListener('change', () => {
            if (selCartera.value === 'suelta') {
                bloqueCompra.style.display = 'flex';
                if(bloquePeso) bloquePeso.style.display = 'none'; // Oculta peso si es individual
            } else {
                bloqueCompra.style.display = 'none';
                if(bloquePeso) bloquePeso.style.display = 'block'; // Pide peso si pertenece a cartera
            }
        });
        // Disparo artificial para sincronizar el estado inicial al abrir el modal
        selCartera.dispatchEvent(new Event('change'));
    }

    // Efecto Acordeón para colapsar/desplegar posiciones dentro de una cartera
    document.querySelectorAll('.clickable-header').forEach(header => {
        header.addEventListener('click', (e) => {
            // Evita colapsar si pulsamos un botón de acción en la cabecera
            if (e.target.closest('.btn-action') || e.target.closest('.item-actions')) return;
            
            const list = header.nextElementSibling;
            if (list) {
                list.classList.toggle('collapsed');
                header.querySelector('.toggle-icon')?.classList.toggle('rotated');
            }
        });
    });

    // =========================================================================
    // PREPARACIÓN DE MODALES ESPECÍFICOS CON DATOS (DATA-ATTRIBUTES)
    // =========================================================================

    document.querySelectorAll('.btnTraspasoCartera').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.getElementById('tc_cartera_id').value = e.currentTarget.dataset.id;
            document.getElementById('tc_nombre_label').innerText = e.currentTarget.dataset.nombre;
            document.getElementById('modalTraspasoCartera').style.display = 'flex';
        });
    });

    document.querySelectorAll('.btnRetirarInversion').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.getElementById('ri_cartera_id').value = e.currentTarget.dataset.id;
            document.getElementById('modalRetirarInversion').style.display = 'flex';
        });
    });

    document.querySelectorAll('.btnVenderPosicion').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.getElementById('venta_ticker').value = e.currentTarget.dataset.ticker;
            document.getElementById('venta_cartera_id').value = e.currentTarget.dataset.cartera;
            document.getElementById('venta_ticker_label').innerText = `Vendiendo: ${e.currentTarget.dataset.ticker} (A Mercado)`;
            document.getElementById('venta_cantidad').max = e.currentTarget.dataset.max;
            document.getElementById('venta_cantidad').value = e.currentTarget.dataset.max;
            document.getElementById('modalVenderPosicion').style.display = 'flex';
        });
    });

    document.querySelectorAll('.btnEditarPeso').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.getElementById('ep_cartera_id').value = e.currentTarget.dataset.cartera;
            document.getElementById('ep_ticker').value = e.currentTarget.dataset.ticker;
            document.getElementById('ep_peso').value = e.currentTarget.dataset.peso;
            document.getElementById('editar_peso_label').innerText = `Actualizando: ${e.currentTarget.dataset.ticker}`;
            document.getElementById('modalEditarPeso').style.display = 'flex';
        });
    });

    // Acción directa: Botón de Reajuste Automático
    document.querySelectorAll('.btnReajustarCartera').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            if(confirm("¿Reajustar pesos a mercado? Se ejecutarán compras y ventas automáticas.")) {
                const res = await fetch('/reajustar_cartera', { 
                    method: 'POST', 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify({ cartera_id: e.currentTarget.dataset.id }) 
                });
                if(res.ok) location.reload();
            }
        });
    });

    // =========================================================================
    // SISTEMA UNIFICADO DE PETICIONES AL SERVIDOR (FETCH)
    // =========================================================================

    /**
     * Intercepta el submit de cualquier formulario, construye el JSON
     * dinámicamente mapeando los 'id' de los inputs y hace la petición al servidor.
     */
    const enviarForm = async (id, url, method = 'POST') => {
        const form = document.getElementById(id);
        if(!form) return;
        
        form.addEventListener('submit', async (e) => {
            e.preventDefault();
            const btn = form.querySelector('.btn-guardar');
            btn.disabled = true;
            const originalText = btn.innerText;
            btn.innerText = "Procesando...";

            const formData = {};
            // Mapeo genérico de IDs (Ej: 'edit_concepto' -> 'concepto')
            form.querySelectorAll('input, select').forEach(i => { 
                if(i.id) formData[i.id.split('_').slice(1).join('_')] = i.value; 
            });

            // Excepciones manuales para formularios que no siguen el patrón
            if(id === 'formCrearCartera') {
                formData['nombre'] = document.getElementById('nombre_cartera').value;
            }
            if(id === 'formAgregarPosicion') {
                formData['cartera_id'] = selCartera.value;
                formData['ticker'] = document.getElementById('posicion_ticker').value;
                formData['cantidad'] = document.getElementById('posicion_cantidad').value || 0;
                formData['precio_compra'] = document.getElementById('posicion_precio').value || 0;
                formData['peso_objetivo'] = document.getElementById('posicion_peso').value || 0;
            }
            if(id === 'formRetirarInversion') {
                formData['direccion'] = 'desde_inversion';
            }

            try {
                const res = await fetch(url, { 
                    method: method, 
                    headers: {'Content-Type': 'application/json'}, 
                    body: JSON.stringify(formData) 
                });
                const json = await res.json();
                if(res.ok) {
                    location.reload(); 
                } else {
                    alert(json.error || json.mensaje || "Error procesando la solicitud.");
                }
            } catch(error) { 
                alert("Error crítico de conexión."); 
            } finally { 
                btn.disabled = false; 
                btn.innerText = originalText;
            }
        });
    };

    // Inicializamos todos los procesos
    enviarForm('formCrearCartera', '/crear_cartera');
    enviarForm('formAgregarPosicion', '/agregar_posicion');
    enviarForm('formTraspasoCartera', '/traspaso_cartera');
    enviarForm('formRetirarInversion', '/traspaso_cartera'); 
    enviarForm('formEditarPeso', '/actualizar_peso', 'PUT');
    enviarForm('formVenderPosicion', '/vender_posicion');
    enviarForm('formTraspasoBroker', '/traspaso_broker');

    // =========================================================================
    // PRECIOS LIVE: MOTOR DE ACTUALIZACIÓN EN TIEMPO REAL
    // =========================================================================

    /**
     * Busca todos los Tickers en la pantalla, pide a la API los precios actuales
     * y recalcula las inversiones (Ganancias/Pérdidas) sin refrescar la web.
     */
    const actualizarPreciosLive = async () => {
        const elementos = document.querySelectorAll('.posicion-item');
        if (elementos.length === 0) return;

        const tickersSet = new Set();
        elementos.forEach(el => tickersSet.add(el.dataset.ticker));

        try {
            const response = await fetch('/api/precios_live', { 
                method: 'POST', 
                headers: { 'Content-Type': 'application/json' }, 
                body: JSON.stringify({ tickers: Array.from(tickersSet) }) 
            });
            const precios_live = await response.json();

            elementos.forEach(el => {
                const ticker = el.dataset.ticker;
                const cartera = el.dataset.cartera;
                const qty = parseFloat(el.dataset.cantidad);
                const p_compra = parseFloat(el.dataset.compra);

                const pSpan = document.getElementById(`live-price-${cartera}-${ticker}`);
                const vSpan = document.getElementById(`live-value-${cartera}-${ticker}`);
                const pnlSpan = document.getElementById(`live-pnl-${cartera}-${ticker}`);
                
                if (precios_live[ticker]) {
                    const actual = precios_live[ticker];
                    const v_actual = actual * qty;
                    const invertido = p_compra * qty;
                    // Cálculo matemático del P&L
                    const pnl_pct = invertido > 0 ? ((v_actual - invertido) / invertido) * 100 : 0;
                    
                    // Actualización del DOM
                    if(pSpan) { 
                        pSpan.innerText = `Actual: ${actual.toFixed(4)}€`; 
                        pSpan.classList.remove('loading-price'); 
                    }
                    if(vSpan) {
                        vSpan.innerText = `${v_actual.toFixed(2)}€`;
                    }
                    if(pnlSpan) {
                        pnlSpan.innerText = qty === 0 ? "0.00% P&L" : `${pnl_pct > 0 ? '+' : ''}${pnl_pct.toFixed(2)}% P&L`;
                        pnlSpan.className = qty === 0 ? 'posicion-subtext' : (v_actual > invertido ? 'posicion-subtext text-profit' : 'posicion-subtext text-loss');
                    }
                }
            });
        } catch (error) {
            console.error("Error recuperando precios live:", error);
        }
    };

    // Disparamos la actualización al cargar la vista
    actualizarPreciosLive();
    // Y definimos un polling cíclico cada 15 segundos
    setInterval(actualizarPreciosLive, 15000);
});