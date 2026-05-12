document.addEventListener('DOMContentLoaded', () => {
    // Al pulsar editar en la lista, rellenar y abrir el modal
    document.querySelectorAll('.btnEditarMovimiento').forEach(btn => {
        btn.addEventListener('click', (e) => {
            const d = e.currentTarget.dataset;
            document.getElementById('edit_id').value = d.id;
            document.getElementById('edit_concepto').value = d.concepto;
            document.getElementById('edit_cantidad').value = d.cantidad;
            document.getElementById('edit_categoria').value = d.categoria;
            document.getElementById('edit_fecha').value = d.fecha;
            document.getElementById('modalEditar').style.display = 'flex';
        });
    });

    // Enviar los datos editados al backend mediante PUT
    document.getElementById('formEditarMovimiento').addEventListener('submit', async (e) => {
        e.preventDefault();
        const id = document.getElementById('edit_id').value;
        const data = { 
            concepto: document.getElementById('edit_concepto').value, 
            cantidad: document.getElementById('edit_cantidad').value, 
            categoria: document.getElementById('edit_categoria').value, 
            fecha: document.getElementById('edit_fecha').value 
        };
        try {
            const res = await fetch(`/editar_movimiento/${id}`, { 
                method: 'PUT', 
                headers: {'Content-Type': 'application/json'}, 
                body: JSON.stringify(data) 
            });
            if(res.ok) {
                location.reload();
            } else {
                alert("Ocurrió un error al editar la transacción.");
            }
        } catch (error) {
            console.error("Error de conexión:", error);
        }
    });

    // Lógica para borrar permanentemente un movimiento
    document.querySelectorAll('.btnEliminarMovimiento').forEach(btn => {
        btn.addEventListener('click', async (e) => {
            if(confirm("¿Seguro que deseas eliminar permanentemente este movimiento?")) {
                try {
                    const res = await fetch(`/eliminar_movimiento/${e.currentTarget.dataset.id}`, { method: 'DELETE' });
                    if(res.ok) {
                        location.reload();
                    } else {
                        alert("Error al intentar eliminar el registro.");
                    }
                } catch (error) {
                    console.error("Fallo de red:", error);
                }
            }
        });
    });
});
/* Sincronizacion final */