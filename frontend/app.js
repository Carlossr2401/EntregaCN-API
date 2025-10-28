// --- CONFIGURACIÓN DINÁMICA ---
// La URL de la API se toma desde el input del HTML
const APIInput = document.getElementById('api-url');
const PASSWORDInput = document.getElementById('api-password'); // Si usas contraseña

// Referencias a los elementos del DOM
const form = document.getElementById('form-crear-nota');
const listaNotas = document.getElementById('lista-notas');

/**
 * 1. Cargar y mostrar todas las notas (GET ALL)
 */
async function cargarNotas() {
    const API_URL = APIInput.value.trim();
    if (!API_URL) {
        listaNotas.innerHTML = '<li>Introduce la URL de la API.</li>';
        return;
    }

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
    e.preventDefault(); 
    const API_URL = APIInput.value.trim();
    if (!API_URL) {
        alert('Introduce la URL de la API antes de crear una nota.');
        return;
    }

    const clase = document.getElementById('clase').value;
    const alumno = document.getElementById('alumno').value;
    const nota = parseInt(document.getElementById('nota').value);

    const nuevaNota = { Clase: clase, Alumno: alumno, Nota: nota };

    try {
        const response = await fetch(API_URL, {
            method: 'POST',
            headers: { 'Content-Type': 'application/json' },
            body: JSON.stringify(nuevaNota)
        });

        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.details || `Error HTTP: ${response.status}`);
        }

        form.reset();
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
    if (!e.target.classList.contains('delete-btn')) return;

    const API_URL = APIInput.value.trim();
    if (!API_URL) {
        alert('Introduce la URL de la API antes de borrar una nota.');
        return;
    }

    const idParaBorrar = e.target.dataset.id;
    if (!confirm(`¿Seguro que quieres borrar la nota con ID: ${idParaBorrar}?`)) return;

    try {
        const response = await fetch(`${API_URL}/${idParaBorrar}`, { method: 'DELETE' });
        if (!response.ok) {
            const errorData = await response.json();
            throw new Error(errorData.error || `Error HTTP: ${response.status}`);
        }
        cargarNotas();
    } catch (error) {
        console.error('Error al borrar nota:', error);
        alert(`Error al borrar: ${error.message}`);
    }
}

// --- INICIALIZACIÓN ---
document.addEventListener('DOMContentLoaded', cargarNotas);
form.addEventListener('submit', crearNota);
listaNotas.addEventListener('click', borrarNota);
