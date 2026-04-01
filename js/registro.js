// Seleccion de elementos por su ID 
const userField = document.getElementById('user');
const passField = document.getElementById('pass');

// Función para validar la longitud
function validarCampo(campo, minimo) {
    if (campo.value.length > 0 && campo.value.length < minimo) {
        campo.style.borderColor = "#E74C3C"; 
    } else if (campo.value.length >= minimo) {
        campo.style.borderColor = "#2ECC71"; 
    } else {
        campo.style.borderColor = ""; // Color por defecto si está vacío
    }
}

userField.addEventListener('keyup', () => validarCampo(userField, 3));
passField.addEventListener('keyup', () => validarCampo(passField, 6));