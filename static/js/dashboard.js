document.addEventListener('DOMContentLoaded', () => {

    // =========================================================================
    // CONFIGURACIÓN INICIAL
    // =========================================================================
    
    // Registro del plugin de DataLabels necesario para los % de la Rosca
    if (typeof ChartDataLabels !== 'undefined') {
        Chart.register(ChartDataLabels);
    }

    Chart.defaults.color = '#95A5A6';
    Chart.defaults.font.family = 'Poppins';

    // =========================================================================
    // GESTIÓN DE MODALES
    // =========================================================================

    const safeOpenModal = (btnId, modalId) => {
        const btn = document.getElementById(btnId);
        const modal = document.getElementById(modalId);
        if (btn && modal) {
            btn.addEventListener('click', () => modal.style.display = 'flex');
        }
    };

    // Asignación de aperturas de modales estándar
    safeOpenModal('btnIngreso', 'modalMovimiento');
    safeOpenModal('btnGasto', 'modalMovimiento');
    safeOpenModal('btnConfig', 'modalConfig');
    safeOpenModal('btnAñadirCuenta', 'modalCuenta');
    safeOpenModal('btnGestionCuentas', 'modalGestionCuentas');

    // Lógica específica para adaptar el modal de Ingreso/Gasto
    document.getElementById('btnIngreso')?.addEventListener('click', () => {
        document.getElementById('modalTitulo').innerText = 'Nuevo Ingreso';
        document.getElementById('tipo_movimiento').value = 'ingreso';
        document.getElementById('grupoCategoria').style.display = 'none';
    });

    document.getElementById('btnGasto')?.addEventListener('click', () => {
        document.getElementById('modalTitulo').innerText = 'Nuevo Gasto';
        document.getElementById('tipo_movimiento').value = 'gasto';
        document.getElementById('grupoCategoria').style.display = 'block';
    });

    // Cierre genérico de cualquier modal
    document.querySelectorAll('.btn-cancelar, #btnCancelarModal, #btnCancelarConfig').forEach(btn => {
        btn.addEventListener('click', () => {
            document.querySelectorAll('.modal-overlay').forEach(m => m.style.display = 'none');
        });
    });

    // =========================================================================
    // ENVÍO DE FORMULARIOS AL BACKEND
    // =========================================================================

    // Envío del formulario de Movimientos (Ingresos/Gastos)
    document.getElementById('formMovimiento')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            tipo: document.getElementById('tipo_movimiento').value,
            concepto: document.getElementById('concepto').value,
            cantidad: document.getElementById('cantidad').value,
            categoria: document.getElementById('tipo_movimiento').value === 'ingreso' ? 'ingreso' : document.getElementById('categoria').value,
            cuenta_id: document.getElementById('cuenta_id').value,
            fecha: document.getElementById('fecha').value
        };
        try {
            const res = await fetch('/movimiento', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(data) 
            });
            if(res.ok) location.reload();
        } catch(err) {
            console.error("Error al enviar movimiento:", err);
        }
    });

    // Envío del formulario de nueva Cuenta Bancaria
    document.getElementById('formCuenta')?.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            nombre: document.getElementById('nombre_cuenta').value,
            tipo: document.getElementById('tipo_cuenta').value,
            saldo: document.getElementById('saldo_inicial').value
        };
        try {
            const res = await fetch('/crear_cuenta', { 
                method: 'POST', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(data) 
            });
            if(res.ok) location.reload();
        } catch(err) {
            console.error("Error al crear cuenta:", err);
        }
    });

    // =========================================================================
    // INICIALIZACIÓN DE GRÁFICOS ESTATICOS (CHART.JS)
    // =========================================================================

    // 1. Gráfico de Evolución Principal (Línea)
    const ctxMain = document.getElementById('mainLineChart');
    if (ctxMain) {
        window.mainChart = new Chart(ctxMain, {
            type: 'line',
            data: { 
                labels: [], 
                datasets: [{ 
                    label: 'Valor', 
                    data: [], 
                    borderColor: '#00A8FF', 
                    borderWidth: 2, 
                    pointRadius: 0, 
                    pointHoverRadius: 6, 
                    pointBackgroundColor: '#00A8FF', 
                    fill: false, 
                    tension: 0.1 
                }] 
            },
            options: {
                responsive: true, 
                maintainAspectRatio: false,
                layout: { padding: { top: 40, bottom: 5, left: -5, right: -5 } },
                plugins: {
                    legend: { display: false },
                    datalabels: { display: false }, // Desactivado para no ensuciar la línea
                    tooltip: { 
                        mode: 'index', 
                        intersect: false, 
                        backgroundColor: '#1A222F', 
                        titleColor: '#95A5A6', 
                        bodyColor: '#fff', 
                        borderColor: 'rgba(255,255,255,0.1)', 
                        borderWidth: 1,
                        callbacks: {
                            title: (items) => items[0].label,
                            label: (item) => ` Valor: ${item.parsed.y.toFixed(2)} €`
                        }
                    }
                },
                scales: {
                    x: { 
                        display: true, 
                        grid: { display: false, drawBorder: true, borderColor: 'rgba(255,255,255,0.1)', borderDash: [5, 5] }, 
                        ticks: { display: false } 
                    },
                    y: { display: false, grid: { display: false }, ticks: { display: false } }
                }
            }
        });
    }

    // 2. Gráfico de Distribución (Barras - Presupuesto vs Gasto)
    const ctxDist = document.getElementById('graficoDistribucion');
    if (ctxDist) {
        const pFijo = parseFloat(ctxDist.dataset.pfijo) || 0, pOcio = parseFloat(ctxDist.dataset.pocio) || 0, pAhorro = parseFloat(ctxDist.dataset.pahorro) || 0;
        const gFijo = parseFloat(ctxDist.dataset.gfijo) || 0, gOcio = parseFloat(ctxDist.dataset.gocio) || 0, gAhorro = parseFloat(ctxDist.dataset.gahorro) || 0;
        new Chart(ctxDist, {
            type: 'bar',
            data: { 
                labels: ['Gastos Fijos', 'Ocio', 'Ahorro / Inversión'], 
                datasets: [
                    { label: 'Presupuestado', data: [pFijo, pOcio, pAhorro], backgroundColor: 'rgba(149, 165, 166, 0.3)', borderRadius: 5 }, 
                    { label: 'Gastado Mensual', data: [gFijo, gOcio, gAhorro], backgroundColor: ['#E74C3C', '#F39C12', '#2ECC71'], borderRadius: 5 }
                ] 
            },
            options: {
                responsive: true, maintainAspectRatio: false,
                plugins: { 
                    legend: { position: 'top', labels: { boxWidth: 15 } }, 
                    datalabels: { display: true, color: '#fff', anchor: 'end', align: 'top', font: { weight: 'bold' }, formatter: (v) => v > 0 ? v + ' €' : '' } 
                },
                scales: { 
                    y: { beginAtZero: true, grid: { color: 'rgba(255,255,255,0.05)' } }, 
                    x: { grid: { display: false } } 
                }
            }
        });
    }

    // 3. Gráfico Rosca (Distribución de Capital con Porcentajes)
    const ctxRosca = document.getElementById('graficoRosca');
    if (ctxRosca) {
        const nombres = JSON.parse(ctxRosca.dataset.nombres || '[]');
        const saldos = JSON.parse(ctxRosca.dataset.saldos || '[]');
        const colores = JSON.parse(ctxRosca.dataset.colores || '[]');
        
        new Chart(ctxRosca, {
            type: 'doughnut',
            data: { labels: nombres, datasets: [{ data: saldos, backgroundColor: colores, borderWidth: 2, borderColor: '#1A222F' }] },
            options: {
                responsive: true, maintainAspectRatio: false, cutout: '70%',
                plugins: {
                    legend: { position: 'right', labels: { boxWidth: 15, padding: 15 } },
                    tooltip: {
                        callbacks: {
                            label: function(context) {
                                let label = context.label || '';
                                if (label) { label += ': '; }
                                if (context.parsed !== null) { label += context.parsed.toFixed(2) + ' €'; }
                                let sum = 0;
                                context.chart.data.datasets[0].data.forEach((val, i) => {
                                    if (context.chart.getDataVisibility(i)) sum += val;
                                });
                                let pct = sum > 0 ? (context.parsed * 100 / sum).toFixed(1) + '%' : '0%';
                                return label + ' (' + pct + ')';
                            }
                        }
                    },
                    datalabels: { 
                        display: true, 
                        color: '#fff', 
                        font: { weight: 'bold', size: 12 }, 
                        formatter: (value, ctx) => {
                            let sum = 0;
                            ctx.chart.data.datasets[0].data.forEach((val, i) => { if (ctx.chart.getDataVisibility(i)) sum += val; });
                            return sum > 0 ? (value * 100 / sum).toFixed(1) + '%' : '';
                        }
                    }
                }
            },
            plugins: [{
                id: 'textCenter',
                beforeDraw: function(chart) {
                    const ctx = chart.ctx; ctx.restore();
                    let sum = 0; 
                    chart.data.datasets[0].data.forEach((val, i) => { if (chart.getDataVisibility(i)) sum += val; });
                    const meta = chart.getDatasetMeta(0);
                    if (!meta || !meta.data || !meta.data.length) return;
                    
                    // Cálculo matemático del centro de la rosca
                    const centerX = meta.data[0].x, centerY = meta.data[0].y;
                    ctx.font = "bold 1.2rem Poppins"; ctx.fillStyle = "#fff"; ctx.textAlign = "center"; ctx.textBaseline = "middle";
                    ctx.fillText(sum.toFixed(2) + " €", centerX, centerY);
                    ctx.save();
                }
            }]
        });
    }

    // =========================================================================
    // MOTOR DINÁMICO DEL GRÁFICO PRINCIPAL (LÍNEA Y FILTROS)
    // =========================================================================

    let currentType = 'total';
    let currentId = '';
    let currentPeriod = '1d';

    const periodLabels = { 
        '1d': 'ÚLTIMAS 24 HORAS', 
        '1w': 'SEMANA PASADA', 
        '1mo': 'ÚLTIMO MES', 
        '3mo': 'ÚLTIMOS 3 MESES', 
        'ytd': 'AÑO HASTA LA FECHA', 
        '1y': 'ÚLTIMO AÑO', 
        'max': 'HISTÓRICO TOTAL' 
    };

    /**
     * Recupera los datos del backend según los filtros seleccionados
     * y repinta el gráfico principal.
     */
    const updateDashboardChart = async () => {
        try {
            const res = await fetch(`/api/historico?tipo=${currentType}&id=${currentId}&periodo=${currentPeriod}`);
            const data = await res.json();
            
            if (data.labels && data.values && data.values.length > 0) {
                // Actualiza datos de la línea
                window.mainChart.data.labels = data.labels;
                window.mainChart.data.datasets[0].data = data.values;
                
                // Genera un padding automático superior para evitar que la línea choque
                const maxVal = Math.max(...data.values);
                const minVal = Math.min(...data.values);
                const padding = (maxVal - minVal) * 0.5; 
                window.mainChart.options.scales.y.suggestedMax = maxVal + padding;
                window.mainChart.options.scales.y.suggestedMin = minVal > padding ? minVal - padding : 0;
                
                window.mainChart.update();
                
                // Actualiza textos numéricos en pantalla
                document.getElementById('mainValueDisplay').innerText = data.current_value.toFixed(2) + ' €';
                
                if (data.depositos !== undefined) {
                    const badge = document.getElementById('badgeDepositos');
                    if(badge) badge.innerText = data.depositos.toFixed(2) + ' € DEPÓSITOS NETOS';
                }

                // Cálculo visual de ganancias/pérdidas
                const changeEl = document.getElementById('periodChangeDisplay');
                const yieldEl = document.getElementById('mainYieldDisplay');
                const sign = data.change_eur >= 0 ? '↗ +' : '↘ ';
                
                changeEl.innerText = `${sign}${Math.abs(data.change_eur).toFixed(2)} €`;
                yieldEl.innerText = `${sign}${Math.abs(data.change_pct).toFixed(2)} %`;
                changeEl.className = 'broker-value-change ' + (data.change_eur >= 0 ? 'text-profit' : 'text-loss');
                yieldEl.className = 'broker-value-change ' + (data.change_eur >= 0 ? 'text-profit' : 'text-loss');
            } else {
                // Estado vacío si no hay histórico
                window.mainChart.data.labels = ['Sin datos'];
                window.mainChart.data.datasets[0].data = [0];
                window.mainChart.update();
                document.getElementById('mainValueDisplay').innerText = '0.00 €';
                document.getElementById('periodChangeDisplay').innerText = '0.00 €';
                document.getElementById('mainYieldDisplay').innerText = '0.00 %';
                document.getElementById('periodChangeDisplay').className = 'broker-value-change text-profit';
                document.getElementById('mainYieldDisplay').className = 'broker-value-change text-profit';
                if (data.depositos !== undefined) {
                    const badge = document.getElementById('badgeDepositos');
                    if(badge) badge.innerText = data.depositos.toFixed(2) + ' € DEPÓSITOS NETOS';
                }
            }
        } catch (e) { console.error("Error al actualizar la gráfica de la dashboard:", e); }
    };

    // Eventos para la botonera de tiempo (1D, 1S, 1M, etc)
    document.querySelectorAll('.btn-time').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-time').forEach(b => b.classList.remove('active'));
            e.target.classList.add('active');
            currentPeriod = e.target.dataset.period;
            document.getElementById('periodLabel').innerText = periodLabels[currentPeriod];
            updateDashboardChart();
        });
    });

    // Eventos para los botones laterales de Carteras/Posiciones
    document.querySelectorAll('.btn-wallet').forEach(btn => {
        btn.addEventListener('click', (e) => {
            document.querySelectorAll('.btn-wallet').forEach(b => b.classList.remove('btn-active'));
            e.target.classList.add('btn-active');
            currentType = e.target.dataset.type;
            currentId = e.target.dataset.id || '';
            
            // Actualiza el título del gráfico
            let entityName = "VALOR DE LA CUENTA";
            if(currentType === 'cartera' || currentType === 'posicion') {
                entityName = e.target.innerText.toUpperCase();
            }
            document.getElementById('chartEntityLabel').innerText = entityName;
            
            updateDashboardChart();
        });
    });

    // Inicialización del motor en el arranque de la vista
    updateDashboardChart();
    
    // Polling recurrente para sensación de Tiempo Real (15 seg)
    setInterval(updateDashboardChart, 15000);
});