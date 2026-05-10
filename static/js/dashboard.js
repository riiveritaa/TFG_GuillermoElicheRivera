document.addEventListener('DOMContentLoaded', () => {
    const modal = document.getElementById('modalMovimiento');
    const form = document.getElementById('formMovimiento');
    const modalTitulo = document.getElementById('modalTitulo');
    const tipoHidden = document.getElementById('tipo_movimiento');
    const inputFecha = document.getElementById('fecha');
    const grupoCategoria = document.getElementById('grupoCategoria');
    const selectCategoria = document.getElementById('categoria');

    const modalConfig = document.getElementById('modalConfig');
    const formConfig = document.getElementById('formConfig');
    
    const btnNuevoIngreso = document.getElementById('btnIngreso');
    const btnNuevoGasto = document.getElementById('btnGasto');
    const btnConfig = document.getElementById('btnConfig');
    const btnCancelar = document.getElementById('btnCancelarModal');
    const btnCancelarConfig = document.getElementById('btnCancelarConfig');

    inputFecha.valueAsDate = new Date();

    const abrirModal = (tipo) => {
        if (tipo === 'ingreso') {
            modalTitulo.innerText = 'Nuevo Ingreso';
            tipoHidden.value = 'ingreso';
            modalTitulo.style.color = '#2ecc71'; 
            grupoCategoria.style.display = 'none'; 
            selectCategoria.value = 'ingreso'; 
        } else {
            modalTitulo.innerText = 'Nuevo Gasto';
            tipoHidden.value = 'gasto';
            modalTitulo.style.color = '#e74c3c'; 
            grupoCategoria.style.display = 'block'; 
            selectCategoria.value = 'fijo';
        }
        modal.style.display = 'flex';
    }

    const cerrarModal = () => {
        modal.style.display = 'none';
        form.reset();
        inputFecha.valueAsDate = new Date();
    }

    btnNuevoIngreso.addEventListener('click', () => abrirModal('ingreso'));
    btnNuevoGasto.addEventListener('click', () => abrirModal('gasto'));
    btnCancelar.addEventListener('click', cerrarModal);

    btnConfig.addEventListener('click', () => modalConfig.style.display = 'flex');
    btnCancelarConfig.addEventListener('click', () => modalConfig.style.display = 'none');

    window.addEventListener('click', (e) => {
        if (e.target === modal) cerrarModal();
        if (e.target === modalConfig) {
            // Al cerrar sin guardar, recargamos la web para que vuelvan a aparecer los porcentajes de la BBDD
            modalConfig.style.display = 'none';
            location.reload(); 
        }
    });

    // Envío Movimiento
    form.addEventListener('submit', async (e) => {
        e.preventDefault();
        const data = {
            tipo: tipoHidden.value,
            concepto: document.getElementById('concepto').value,
            cantidad: parseFloat(document.getElementById('cantidad').value),
            categoria: selectCategoria.value,
            fecha: inputFecha.value
        };

        try {
            const response = await fetch('/movimiento', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify(data)
            });
            if (response.ok) {
                alert('¡Movimiento guardado!');
                location.reload();
            }
        } catch(error) {
            console.error('Error:', error);
        }
    });

    // Envío Configuración (Porcentajes)
    formConfig.addEventListener('submit', async (e) => {
        e.preventDefault();

        // Validar que sumen 100%
        const f = parseFloat(document.getElementById('pct_fijo').value) || 0;
        const o = parseFloat(document.getElementById('pct_ocio').value) || 0;
        const a = parseFloat(document.getElementById('pct_ahorro').value) || 0;

        if (f + o + a !== 100) {
            alert(`La suma actual es ${f + o + a}%. Los porcentajes deben sumar exactamente 100%.`);
            return; // Bloqueamos el guardado
        }

        try {
            const response = await fetch('/configurar_porcentajes', {
                method: 'POST',
                headers: {'Content-Type': 'application/json'},
                body: JSON.stringify({ pct_fijo: f, pct_ocio: o, pct_ahorro: a })
            });
            
            const result = await response.json();
            
            if (response.ok) {
                alert('¡Porcentajes guardados correctamente!');
                modalConfig.style.display = 'none';
            } else {
                alert('Error: ' + result.mensaje);
            }
        } catch(error) {
            console.error('Error:', error);
            alert('Hubo un error de conexión al guardar los porcentajes.');
        }
    });
});