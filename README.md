# Tic-Tac-Toe IA – Plataforma Web para Análisis y Evaluación de Jugadas

- Repositorio: https://github.com/OmarGuerra1999/Tic-Tac-Toe
- Página Web: https://tic-tac-toe-peln.onrender.com/


---
## Descripción

Tic-Tac-Toe IA es una plataforma web diseñada para analizar, evaluar y mejorar jugadas del clásico juego Tres en Raya. A través de un motor de inteligencia artificial y una interfaz intuitiva, los usuarios pueden ingresar jugadas, recibir evaluaciones basadas en rúbricas estructuradas, y consultar historial de partidas y patrones comunes.

El sistema está desarrollado con Python y Flask para la lógica backend, SQLite para almacenamiento de datos, y tecnologías web modernas para la interfaz, facilitando tanto la interacción como el análisis avanzado de jugadas.

---

## Características Principales

- Motor IA inteligente: Algoritmos que evalúan el tablero, sugieren jugadas óptimas y detectan ganadores.
- Evaluación estructurada: Rúbricas objetivas para calificar jugadas según criterios definidos.
- Historial completo: Registro de evaluaciones pasadas con detalles y observaciones.
- Importación de datos: Capacidad para cargar grandes conjuntos de jugadas desde archivos CSV.
- Interfaz amigable y responsive: Compatible con dispositivos móviles y escritorio.
- Almacenamiento dual: Uso combinado de base de datos SQLite y archivos JSON para flexibilidad.

---

## Estructura del Proyecto y Funcionalidades Clave

| Archivo / Módulo         | Funcionalidad Principal                                                    |
| ------------------------ | -------------------------------------------------------------------------- |
| **app.py**               | Controlador principal de la aplicación, rutas web y lógica base.           |
| **juego\_ia.py**         | Motor de IA para análisis y toma de decisiones en el juego.                |
| **db\_handler.py**       | Gestión y conexión con base de datos SQLite.                               |
| **consulta\_jugadas.py** | Consultas y análisis sobre jugadas y evaluaciones previas.                 |
| **import\_csv.py**       | Importación de datos desde archivos CSV para alimentar el sistema.         |
| **templates/**           | Plantillas HTML para las páginas web (`index.html`, `evaluar.html`, etc.). |
| **dataset1.csv**         | Conjunto de datos de jugadas para análisis o entrenamiento.                |
| **jugadas.json**         | Registro en JSON de jugadas almacenadas.                                   |
| **evaluaciones.json**    | Evaluaciones previas en formato JSON.                                      |
| **coincidencias.json**   | Patrón de jugadas repetidas almacenadas.                                   |

---

## Tecnologías Utilizadas

- Python 3.8+
- Flask: Framework web ligero para Python.
- SQLite: Base de datos ligera para almacenamiento local.
- HTML5, CSS3, Bootstrap: Diseño y estructura web responsive.
- JavaScript (Chart.js): Visualización gráfica interactiva.
- Pandas: Para manejo y análisis de datos CSV.

---

## Instalación y Ejecución Local

1. Clonar el repositorio:
   
   git clone https://github.com/OmarGuerra1999/Tic-Tac-Toe.git
   
   cd Tic-Tac-Toe

2. Crear y activar un entorno virtual (opcional pero recomendado):

   python3 -m venv venv

   source venv/bin/activate   # Windows: venv\Scripts\activate

3. Instalar las dependencias:
   
   pip install -r requirements.txt

4. Ejecutar la aplicación:

   python app.py

5. Abrir navegador y acceder a:

   http://localhost:5000

---

## Cómo Desplegar en Otro Servidor

Para levantar esta aplicación en otro servidor (por ejemplo, un VPS, un servidor en la nube o un servicio PaaS):
   
1. Preparar el entorno:
  
    - Instalar Python 3.8+ y SQLite.
    - Clonar el repositorio en el servidor.
    - Configurar entorno virtual y dependencias (como en Instalación Local).

2. Configurar servidor de aplicaciones:

    - Usar un servidor WSGI como Gunicorn para producción.
    
        pip install gunicorn
        
        gunicorn app:app --bind 0.0.0.0:8000

3. Configurar un proxy inverso:

    - Instalar y configurar Nginx o Apache para manejar peticiones HTTP y HTTPS, redirigiendo al Gunicorn.
    - Esto ofrece estabilidad, seguridad y manejo de certificados SSL.

4. Abrir puertos y firewall:

    - Asegurarse que el puerto HTTP (80) o HTTPS (443) esté abierto para acceso público.

5. Alternativas para despliegue sencillo:

    - Servicios PaaS como Render.com (como el deploy original), Heroku, Railway o DigitalOcean App Platform que permiten desplegar con pocos comandos y gestionan la infraestructura.

---

## Códigos Clave Trabajados

- app.py: Define rutas web, carga datos JSON, maneja solicitudes GET/POST, renderiza vistas y guarda evaluaciones.
- juego_ia.py: Contiene la lógica para determinar ganador, buscar movimientos libres y elegir la mejor jugada basada en heurísticas.
- db_handler.py: Gestiona conexión y consultas SQL para persistencia en SQLite.
- consulta_jugadas.py: Realiza búsquedas y análisis de jugadas y evaluaciones previas, utilizando datos JSON.
- import_csv.py: Carga datos CSV para alimentar la base de datos y enriquecer el sistema con jugadas históricas.

---



