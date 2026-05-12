/**
 * Lógica de validación visual de campos en el formulario de Registro.
 * Añade bordes dinámicos (Verde/Rojo) al vuelo según las constraints.
 */

document.addEventListener('DOMContentLoaded', () => {
    
    // Selección de elementos del DOM por su ID
    const userField = document.getElementById('user');
    const passField = document.getElementById('pass');

    /**
     * Aplica estilos de validación al borde del input.
     * @param {HTMLElement} campo - El elemento input a validar.
     * @param {number} minimo - La longitud mínima de caracteres permitida.
     */
    function validarCampo(campo, minimo) {
        if (!campo) return; // Prevención de errores si el elemento no existe

        if (campo.value.length > 0 && campo.value.length < minimo) {
            // Inválido: Menos caracteres del mínimo requerido
            campo.style.borderColor = "#E74C3C"; 
        } else if (campo.value.length >= minimo) {
            // Válido: Cumple la longitud
            campo.style.borderColor = "#2ECC71"; 
        } else {
            // Estado inicial/Vacío
            campo.style.borderColor = ""; 
        }
    }

    // Vinculación de los eventos 'keyup' para revisión en tiempo real
    if (userField) {
        userField.addEventListener('keyup', () => validarCampo(userField, 3));
    }
    
    if (passField) {
        passField.addEventListener('keyup', () => validarCampo(passField, 6));
    }
});
/* Sincronizacion final */