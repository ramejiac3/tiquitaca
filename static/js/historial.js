// Mostrar u ocultar el panel lateral de rúbrica
function toggleRubrica() {
  const panel = document.getElementById('rubricaPanel');
  const expanded = panel.classList.toggle('active'); // Alterna clase "active"
  panel.setAttribute('aria-hidden', !expanded); // Accesibilidad: oculta o muestra para lectores de pantalla
}

// Ejecuta cuando el DOM ha sido completamente cargado
document.addEventListener('DOMContentLoaded', () => {
  // Filtro en tiempo real para la tabla
  const filtroInput = document.getElementById("filtro");
  filtroInput.addEventListener("input", function () {
    const val = this.value.toLowerCase(); // Texto del input en minúsculas
    // Itera por cada fila del cuerpo de la tabla
    document.querySelectorAll("tbody tr").forEach(row => {
      // Muestra u oculta la fila dependiendo si incluye el texto del filtro
      row.style.display = row.textContent.toLowerCase().includes(val) ? "" : "none";
    });
  });

  // ---------- GRÁFICO DE RADAR ----------

  // Obtiene las dimensiones y promedios desde el objeto global (inyectado desde backend)
  const dimensiones = window.dimensiones || []; // Ej: ["Comprensión", "Claridad", ...]
  const promedios = window.promedios || {};      // Ej: {"Comprensión": 2.5, "Claridad": 3, ...}

  // Construye un array con los valores de cada dimensión (o 0 si no hay dato)
  const dataValores = dimensiones.map(dim => promedios[dim] || 0);

  // Configuración del gráfico Radar
  const config = {
    type: 'radar',
    data: {
      labels: dimensiones, // Etiquetas del eje radial
      datasets: [{
        label: 'Puntaje promedio',
        data: dataValores, // Datos del gráfico
        fill: true,
        backgroundColor: 'rgba(54, 162, 235, 0.25)',
        borderColor: 'rgb(54, 162, 235)',
        pointBackgroundColor: 'rgb(54, 162, 235)',
        pointBorderColor: '#fff',
        pointHoverBackgroundColor: '#fff',
        pointHoverBorderColor: 'rgb(54, 162, 235)'
      }]
    },
    options: {
      scales: {
        r: {
          beginAtZero: true,
          min: 0,
          max: 3, // Escala de 0 a 3 como en la rúbrica
          ticks: {
            stepSize: 1 // Mostrar 0, 1, 2, 3
          }
        }
      },
      plugins: {
        legend: {
          labels: {
            font: {
              size: 14 // Tamaño de la leyenda
            }
          }
        }
      }
    }
  };

  // Dibuja el gráfico si existe el canvas
  const canvas = document.getElementById('graficoRadar');
  if (canvas) {
    const ctx = canvas.getContext('2d');
    new Chart(ctx, config); // Crea el gráfico usando Chart.js
  }
});
