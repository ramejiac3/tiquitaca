// Variables globales del juego
let jugando = true;            // Indica si la partida está activa
let historial = [];            // Historial de jugadas
let modoAuto = false;          // Indica si el modo automático está activado

// ----- Renderizado del tablero -----
function renderTablero(tablero) {
  const table = document.getElementById("tablero");
  table.innerHTML = ""; // Limpia el contenido anterior

  for (let i = 0; i < 3; i++) {
    const row = document.createElement("tr");
    for (let j = 0; j < 3; j++) {
      const cell = document.createElement("td");
      const value = tablero[i][j];
      if (value !== "b") {
        cell.innerText = value.toUpperCase(); // Coloca X u O
        cell.classList.add(value);           // Clase para estilo
      }
      row.appendChild(cell);
    }
    table.appendChild(row);
  }
}

// ----- Mostrar historial de jugadas -----
function renderHistorial() {
  const div = document.getElementById("historial");
  if (historial.length === 0) {
    div.innerHTML = "<em>No hay jugadas aún.</em>";
    return;
  }

  // Muestra el historial de jugadas con modelo, jugador y razón
  div.innerHTML = historial
    .map(
      (h, idx) =>
        `#${idx + 1}: <b>${h.jugador.toUpperCase()}</b> (${h.modelo}) – ${h.razon}`
    )
    .join("<br>");
}

// ----- Guardar estado actual en sessionStorage -----
function guardarEstado(tableroActual) {
  const estado = {
    tablero: tableroActual,
    historial,
    jugando,
    modoAuto
  };
  sessionStorage.setItem("estado_tres_en_raya", JSON.stringify(estado));
}

// ----- Cargar estado guardado del juego -----
function cargarEstado() {
  const guardado = sessionStorage.getItem("estado_tres_en_raya");
  if (!guardado) return false;

  try {
    const { tablero, historial: hist, jugando: jugandoGuardado, modoAuto: auto } = JSON.parse(guardado);
    historial = hist;
    jugando = jugandoGuardado;
    modoAuto = auto;

    renderTablero(tablero);
    renderHistorial();
    return true;
  } catch (e) {
    console.error("No se pudo restaurar el estado guardado:", e);
    return false;
  }
}

// ----- Ejecutar un turno (modelo realiza una jugada) -----
function jugarTurno() {
  if (!jugando) return;

  fetch("/jugar_turno", { method: "POST" })
    .then((res) => res.json())
    .then((data) => {
      if (data.error) {
        mostrarError("Jugada inválida: " + data.error);
        jugando = false;
        return;
      }

      renderTablero(data.tablero);

      // Mostrar razonamiento del modelo
      document.getElementById("razon").innerHTML = `Jugador <b>${data.jugador.toUpperCase()}</b> (${data.modelo}): ${data.razon}`;

      // Añadir al historial
      historial.push({
        jugador: data.jugador,
        razon: data.razon,
        modelo: data.modelo,
      });
      renderHistorial();

      // Verificar si hay ganador o empate
      if (data.ganador === "empate") {
        document.getElementById("razon").innerHTML += "<br><b>¡Empate!</b>";
        jugando = false;
      } else if (data.ganador) {
        document.getElementById("razon").innerHTML += `<br><b>Ganador: ${data.ganador.toUpperCase()}</b>`;
        jugando = false;
      }

      guardarEstado(data.tablero);

      // Si el modo automático está activo, repetir turno automáticamente
      if (modoAuto && jugando) {
        setTimeout(jugarTurno, 150); // Espera 150 ms
      }
    })
    .catch((err) => {
      mostrarError("Error en la comunicación con el servidor.");
      console.error(err);
      jugando = false;
    });
}

// ----- Activar modo automático -----
function jugarAuto() {
  if (!jugando) return;
  modoAuto = true;
  jugarTurno(); // Empieza a jugar automáticamente
}

// ----- Iniciar nueva partida (resetea tablero e historial) -----
function siguientePartida() {
  fetch("/siguiente_partida", { method: "POST" })
    .then((res) => res.json())
    .then(() => {
      jugando = true;
      modoAuto = false;
      historial = [];

      ocultarError();
      document.getElementById("razon").innerText = "";
      document.getElementById("historial").innerText = "";

      sessionStorage.removeItem("estado_tres_en_raya");

      // Obtener nuevo estado desde el servidor
      fetch("/estado")
        .then((res) => res.json())
        .then((data) => renderTablero(data.tablero));
    })
    .catch((err) => {
      mostrarError("No se pudo reiniciar la partida.");
      console.error(err);
    });
}

// ----- Mostrar mensaje de error -----
function mostrarError(mensaje) {
  const errorDiv = document.getElementById("error-msg");
  errorDiv.textContent = mensaje;
  errorDiv.style.display = "block";
}

// ----- Ocultar mensaje de error -----
function ocultarError() {
  const errorDiv = document.getElementById("error-msg");
  errorDiv.style.display = "none";
}

// ----- Reiniciar completamente el juego (desde cero) -----
function reiniciar() {
  fetch("/reiniciar", { method: "POST" })
    .then(() => {
      jugando = true;
      modoAuto = false;
      historial = [];

      document.getElementById("razon").innerText = "";
      document.getElementById("historial").innerText = "";
      ocultarError();

      sessionStorage.removeItem("estado_tres_en_raya");

      fetch("/estado")
        .then((res) => res.json())
        .then((data) => renderTablero(data.tablero));
    })
    .catch((err) => {
      mostrarError("No se pudo reiniciar el juego.");
      console.error(err);
    });
}

// ----- Cuando carga la página: intenta restaurar estado anterior -----
window.addEventListener("DOMContentLoaded", () => {
  const cargado = cargarEstado(); // Intenta restaurar el estado anterior
  if (!cargado) reiniciar();     // Si no hay, reinicia desde cero
});

