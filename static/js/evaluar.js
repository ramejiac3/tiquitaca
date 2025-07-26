// Función para mostrar u ocultar el panel de la rúbrica
function toggleRubrica() {
  const panel = document.getElementById("rubricaPanel");
  panel.classList.toggle("open"); // Alterna la clase "open" para mostrar/ocultar
}

// Función que valida el formulario de evaluación antes de enviarlo
function validarFormulario() {
  const form = document.querySelector('form[action="/guardar_evaluacion"]');
  if (!form) return true; // Si no existe el formulario, no hace nada

  // Lista de dimensiones a evaluar
  const dimensiones = [
    "Comprensión de Reglas",
    "Validez y Legalidad",
    "Razonamiento Estratégico",
    "Factualidad",
    "Coherencia Explicativa",
    "Claridad Lingüística",
    "Adaptabilidad",
  ];

  // Verifica que al menos una opción esté seleccionada en cada dimensión
  for (const dim of dimensiones) {
    const radios = document.querySelectorAll(`input[name="rubrica[${dim}]"]`);
    const algunoMarcado = [...radios].some((r) => r.checked);
    if (!algunoMarcado) {
      alert(`Por favor, evalúa la dimensión: "${dim}"`);
      return false;
    }
  }

  // Valida que la razón tenga mínimo 3 caracteres
  const razonEl = document.getElementById("razon");
  if (razonEl && razonEl.value.trim().length < 3) {
    alert("Por favor, escribe una explicación más completa.");
    return false;
  }

  return true; // Si todo está correcto, permite enviar
}

// Función para renderizar el tablero dinámicamente en la página
function renderTablero(tablero, movimiento) {
  const contenedor = document.getElementById("tablero-dinamico");
  contenedor.innerHTML = ""; // Limpia el contenido anterior

  const table = document.createElement("table");
  table.className = "tablero";

  for (let i = 0; i < 3; i++) {
    const row = document.createElement("tr");
    for (let j = 0; j < 3; j++) {
      const cell = document.createElement("td");
      const value = tablero[i][j];

      // Agrega el valor al tablero si no está vacío
      if (value !== "b") {
        cell.innerText = value.toUpperCase(); // Muestra "X" o "O"
        cell.classList.add(value); // Agrega clase 'x' o 'o'
      }

      // Resalta la celda marcada por el modelo
      if (
        movimiento &&
        movimiento[0] === "mark" &&
        movimiento[1] - 1 === i &&
        movimiento[2] - 1 === j
      ) {
        cell.classList.add("marcada");
      }

      row.appendChild(cell);
    }
    table.appendChild(row);
  }

  contenedor.appendChild(table); // Agrega el tablero al contenedor
}

// Carga la información de la jugada actual desde el backend
function cargarInfoJugada() {
  fetch("/info_jugada_sesion")
    .then((res) => res.json())
    .then((data) => {
      const contenedor = document.getElementById("info-jugada");

      if (data.error) {
        // Si no hay jugadas disponibles
        contenedor.innerHTML = "<p>No hay jugadas aún.</p>";
      } else {
        // Muestra la información del jugador, modelo y movimiento
        contenedor.innerHTML = `
          <p><strong>Jugador:</strong> ${data.jugador.toUpperCase()}</p>
          <p><strong>Modelo:</strong> ${data.modelo}</p>
          <p><strong>Movimiento:</strong> 
            ${
              Array.isArray(data.movimiento) && data.movimiento[0] === "mark"
                ? `Marcar fila ${data.movimiento[1]}, columna ${data.movimiento[2]}`
                : JSON.stringify(data.movimiento)
            }
          </p>
        `;

        // Actualiza el tablero en sessionStorage si existe estado previo
        const estadoGuardado = sessionStorage.getItem("estado_tres_en_raya");
        if (estadoGuardado) {
          try {
            const estado = JSON.parse(estadoGuardado);
            estado.tablero = data.tablero; // Actualiza el tablero
            sessionStorage.setItem("estado_tres_en_raya", JSON.stringify(estado));
          } catch (e) {
            console.warn("No se pudo actualizar sessionStorage desde /evaluar");
          }
        }
      }
    })
    .catch((err) => {
      console.error("Error al cargar info de la jugada:", err);
      const contenedor = document.getElementById("info-jugada");
      contenedor.innerHTML = "<p class='text-danger'>Error al cargar información de la jugada.</p>";
    });
}

// Evento que se ejecuta cuando la página ha cargado completamente
document.addEventListener("DOMContentLoaded", () => {
  // Obtiene el estado inicial del juego desde el servidor
  fetch("/estado")
    .then((res) => res.json())
    .then((data) => {
      renderTablero(data.tablero, data.movimiento); // Renderiza el tablero actual

      // Guarda el estado en sessionStorage para persistencia local
      const estadoGuardado = sessionStorage.getItem("estado_tres_en_raya");
      if (estadoGuardado) {
        try {
          const estado = JSON.parse(estadoGuardado);
          estado.tablero = data.tablero;
          sessionStorage.setItem("estado_tres_en_raya", JSON.stringify(estado));
        } catch (e) {
          console.warn("No se pudo guardar el tablero en sessionStorage");
        }
      }

      // Carga la información de la jugada
      cargarInfoJugada();
    })
    .catch((err) => {
      console.error("Error al obtener el estado:", err);
    });
});
