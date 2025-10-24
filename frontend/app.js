// --- CONFIGURACIÓN ---
// ¡CAMBIA ESTA IP POR LA IP PÚBLICA DE TU INSTANCIA EC2!
const API_URL = '/api/grades';
// ---------------------

// Referencias a los elementos del DOM
const form = document.getElementById('form-crear-nota');
const listaNotas = document.getElementById('lista-notas');

/**
 * 1. Cargar y mostrar todas las notas (GET ALL)
 */
async function cargarNotas() {
    try {
        const response = await fetch(API_URL);
        if (!response.ok) {
            throw new Error(`Error HTTP: ${response.status}`);
        }
        const notas = await response.json();
        
        // Limpiar la lista antes de añadir
        listaNotas.innerHTML = '';

        // Si no hay notas, mostrar un mensaje
        if (notas.length === 0) {
            listaNotas.innerHTML = '<li>No hay notas registradas.</li>';
            return;
        }

        // Crear un <li> por cada nota
        notas.forEach(nota => {
            const item = document.createElement('li');
            
            // Contenido (Clase, Alumno, Nota)
            const info = document.createElement('div');
            info.className = 'nota-info';
            info.innerHTML = `
                <span>${nota.Clase}</span> (${nota.Alumno}) - 
                <strong>Nota: ${nota.Nota}</strong>
            `;
            
            // Botón de borrar
            const deleteBtn = document.createElement('button');
            deleteBtn.className = 'delete-btn';
            deleteBtn.innerText = 'Borrar 🗑️';
            // Guardamos el ID en el botón para saber cuál borrar
            deleteBtn.dataset.id = nota.id;

            item.appendChild(info);
            item.appendChild(deleteBtn);
            listaNotas.appendChild(item);
        });

    } catch (error) {
        console.error('Error al cargar notas:', error);
        listaNotas.innerHTML = '<li>Error al cargar las notas. Revisa la consola.</li>';
    }
}

/**
 * 2. Crear una nueva nota (POST)
 */
async function crearNota(e) {
    // Prevenir que el formulario recargue la página
    e.preventDefault(); 
    
    // Obtener los valores del formulario
    const clase = document.getElementById('clase').value;
    const alumno = document.getElementById('alumno').value;
    const nota = parseInt(document.getElementById('nota').value);

    const nuevaNota = {
        Clase: clase,
        Alumno: alumno,
        Nota: nota
    };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: {
                'Content-Type': 'application/json'
            },
            body: JSON.stringify(nuevaNota)
        });

        if (!response.ok) {
            // Intentar leer el error de la API
            const errorData = await response.json();
            throw new Error(errorData.details || `Error HTTP: ${response.status}`);
        }

        // Limpiar el formulario
        form.reset();
        
        // Recargar la lista de notas para mostrar la nueva
        cargarNotas();

    } catch (error) {
        console.error('Error al crear la nota:', error);
        alert(`Error al guardar: ${error.message}`);
    }
}

/**
 * 3. Borrar una nota (DELETE)
 */
async function borrarNota(e) {
    // Solo reaccionar si se hizo clic en un botón de borrar
    if (e.target.classList.contains('delete-btn')) {
        
        const idParaBorrar = e.target.dataset.id;
        
        if (!confirm(`¿Seguro que quieres borrar la nota con ID: ${idParaBorrar}?`)) {
            return;
        }

        try {
            const response = await fetch(`${API_URL}/${idParaBorrar}`, {
                method: 'DELETE'
            });

            if (!response.ok) {
                const errorData = await response.json();
                throw new Error(errorData.error || `Error HTTP: ${response.status}`);
            }

            // Recargar la lista para que desaparezca la nota borrada
            cargarNotas();

        } catch (error) {
            console.error('Error al borrar nota:', error);
            alert(`Error al borrar: ${error.message}`);
        }
    }
}


// --- INICIALIZACIÓN ---

// 1. Cargar las notas cuando la página se abre
document.addEventListener('DOMContentLoaded', cargarNotas);

// 2. Escuchar el 'submit' del formulario
form.addEventListener('submit', crearNota);

// 3. Escuchar clics en la lista (para los botones de borrar)
listaNotas.addEventListener('click', borrarNota);