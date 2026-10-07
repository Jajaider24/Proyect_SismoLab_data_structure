# SismoLab AVL — Observatorio sísmico simulado

Proyecto académico de estructuras de datos para gestionar eventos sísmicos ficticios mediante un árbol AVL y estudiar su comportamiento frente a un árbol BST.

## Integrantes

- Joaquín Hoyos Cataño
- Jaider León Díaz

## Objetivo

SismoLab permite registrar, consultar, corregir, revisar, eliminar y archivar eventos de un escenario ficticio. El AVL es el índice central de eventos activos. La aplicación también permite recibir reportes mediante una cola FIFO, conservar acciones para deshacer, cargar y exportar estados JSON, comparar árboles AVL y BST y visualizar eventos en un plano cartesiano.

El escenario y sus clasificaciones son académicos. No constituyen un modelo de predicción ni una evaluación real del riesgo sísmico.

## Reglas principales del dominio

- Identificador entero entre `1` y `999999`, único en el escenario y no reutilizable después de una eliminación.
- Magnitud entre `-2.0` y `10.0`; profundidad entre `0.0` y `700.0` km; coordenadas `x` e `y` entre `0.0` y `1000.0` km.
- El epicentro pertenece a una zona si está dentro de sus límites o en el borde. Si coincide con más de una zona, basta con que una sea poblada para clasificarlo como poblado.
- La prioridad se deriva de magnitud, profundidad y zona poblada: P3 para `M >= 6.0`, o para `M >= 4.5`, `H <= 30.0` y zona poblada; P2 para el resto de `M >= 4.5`; P1 en los demás casos.
- La clave del AVL es la tupla lexicográfica `(prioridad, magnitud, identificador)`. El recorrido inorden presenta las claves en orden ascendente.
- El reloj del escenario se expresa en UTC y se puede avanzar desde la interfaz.
- Los estados de atención son `pending` y `reviewed`. Una creación o corrección aceptada deja el evento pendiente.

## Estructura del proyecto

```text
.
├── main.py                         # Aplicación FastAPI y configuración CORS
├── requirements.txt
├── data/
│   ├── pruebaSimple_AVL.json
│   ├── pruebaSimple_catalogo.json
│   └── casos_minimos/              # Seis escenarios del requerimiento 16
├── src/
│   ├── core/
│   │   ├── AvlTree/                 # AVL, rotaciones, balance y auditoría de bajo nivel
│   │   ├── node/                    # Nodo AVL y validaciones
│   │   ├── structures/              # Pila LIFO y cola FIFO
│   │   └── bst.py                   # BST usado en la comparación
│   ├── models/                      # Evento, clave, zona, estación y reloj
│   ├── controllers/                 # Adaptación de solicitudes a servicios
│   ├── routes/                      # Rutas FastAPI para /avl y /events
│   ├── repository/                  # Lectura de archivos JSON de entrada
│   └── services/
│       ├── eventCatalog_Service.py  # Coordinación del catálogo de eventos
│       └── eventCatalog/            # Índice AVL, reportes, consultas, historial y codec
├── UI/
│   ├── index.html                   # Navegación y vistas principales
│   ├── components/                  # Fragmentos HTML/CSS por componente
│   ├── css/                         # Estilos generales y de vistas
│   └── js/                          # API, servicios, estado, vistas y visualizaciones
└── tests/                           # Pruebas unitarias del proyecto
```

## Arquitectura

- **Estructuras:** AVL y BST implementados en el proyecto; pila explícita para undo y cola FIFO para reportes.
- **Dominio:** `Event`, `EventKey`, `Zone`, `Station` y `SimulationClock` representan los datos del escenario.
- **Backend:** FastAPI expone rutas; los controladores traducen solicitudes HTTP y el catálogo coordina el estado y los servicios especializados.
- **Frontend:** las vistas se dividen en Inicio, Eventos, Reportes y Análisis. Los módulos JavaScript separan navegación, API, formularios, estado, árbol, mapa, reportes, métricas y versiones.
- **Visualización:** D3.js dibuja los árboles y el plano geográfico. El BST se crea para comparación y no reemplaza al AVL operativo.

## Instalación y ejecución local

Desde la carpeta raíz del proyecto, en PowerShell:

```powershell
python -m venv venv
venv\Scripts\Activate.ps1
python -m pip install -r requirements.txt
uvicorn main:app --reload
```

La documentación interactiva de la API queda disponible en:

- <http://127.0.0.1:8000/docs>
- <http://127.0.0.1:8000/redoc>

En otra terminal, inicia la interfaz estática:

```powershell
python -m http.server 5173 --directory UI
```

Abre <http://localhost:5173>. La interfaz requiere que el backend esté activo en `http://localhost:8000`.

## Vistas de la interfaz

- **Inicio:** resumen operativo, actividad, reloj, parámetros y versiones.
- **Eventos:** formulario de alta e importación de nodos, árbol AVL, inspector, operaciones sobre eventos y plano geográfico.
- **Reportes:** recepción e importación de reportes, cola, procesamiento paso a paso o continuo, modo estrés, recuperación y acceso a verificación.
- **Análisis:** consultas del catálogo y comparación gráfica AVL/BST con distintos órdenes de inserción.

La ruta de cada vista se conserva en el fragmento de la URL, por ejemplo `#eventos` o `#analisis`.

El mapa representa `x` horizontalmente y `y` verticalmente en el intervalo `0..1000` km. El origen `(0,0)` está en la esquina inferior izquierda. La imagen de fondo local se selecciona desde el navegador y se almacena en IndexedDB; los puntos muestran eventos activos.

## API de eventos

Todas las rutas de esta sección usan el prefijo `/events`.

### Catálogo y operaciones

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/events` | Crear un evento |
| `POST` | `/events/import-nodes` | Importar una lista de eventos por inserción |
| `GET` | `/events/tree` | Consultar el AVL y sus métricas actuales |
| `GET` | `/events/{identifier}` | Consultar un evento por identificador |
| `PUT` | `/events/{identifier}` | Corregir un evento activo |
| `POST` | `/events/{identifier}/review` | Marcar como revisado |
| `DELETE` | `/events/{identifier}` | Eliminar individualmente |
| `POST` | `/events/{identifier}/archive` | Archivar la rama que nace en un nodo |
| `POST` | `/events/archive/old/preview` | Previsualizar una rama antigua elegible |
| `POST` | `/events/archive/old` | Confirmar el archivo de la rama previsualizada |
| `POST` | `/events/undo` | Deshacer la última acción |

### Reportes y modo de ejecución

| Método | Ruta | Uso |
|---|---|---|
| `POST` | `/events/reports` | Encolar un reporte |
| `POST` | `/events/reports/import` | Encolar un lote de reportes FIFO |
| `POST` | `/events/reports/process/step` | Procesar un reporte |
| `POST` | `/events/reports/process` | Procesar los reportes pendientes |
| `GET` | `/events/mode` | Consultar modo y auditoría del AVL |
| `POST` | `/events/mode` | Cambiar entre normal y estrés |
| `POST` | `/events/recover` | Recuperar el equilibrio del AVL |

### Escenario, estado y versiones

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/events/scenario` | Consultar reloj, parámetros y modo |
| `PUT` | `/events/scenario/parameters` | Actualizar umbral de archivo o zonas |
| `POST` | `/events/clock/advance` | Avanzar el reloj simulado |
| `GET` | `/events/export` | Exportar el estado operativo |
| `POST` | `/events/import` | Cargar un estado exportado |
| `GET` | `/events/versions` | Listar versiones nombradas |
| `POST` | `/events/versions` | Guardar una versión nombrada |
| `POST` | `/events/versions/{name}/restore` | Restaurar una versión |
| `DELETE` | `/events/versions/{name}` | Eliminar una versión |
| `GET` | `/events/history` | Consultar la pila de undo y trazabilidad |
| `GET` | `/events/verify` | Verificar la estructura y referencias |

### Consultas y comparación

| Método | Ruta | Uso |
|---|---|---|
| `GET` | `/events/analysis/pending?k=5` | Pendientes en orden descendente de clave |
| `GET` | `/events/analysis/magnitude?minimum=3&maximum=6` | Intervalo inclusivo de magnitud |
| `GET` | `/events/analysis/depth?maximum_depth=100&start=...&end=...` | Profundidad máxima dentro de fechas |
| `GET` | `/events/analysis/associations/{identifier}` | Consultar asociaciones del evento |
| `GET` | `/events/analysis/costly-high-priority?depth_limit=2` | Consultar eventos P3 por profundidad estructural |
| `GET` | `/events/analysis/compare` | Comparar AVL y BST para varios órdenes |

Los parámetros y ejemplos completos de los cuerpos JSON pueden consultarse en `/docs`.

## API AVL de compatibilidad

El prefijo `/avl` conserva operaciones directas sobre el AVL de nodos:

- `POST /avl/nodes`
- `POST /avl/insert/{value}`
- `PUT /avl/nodes/{identifier}`
- `DELETE /avl/nodes/{identifier}`
- `GET /avl/tree`
- `DELETE /avl/tree`

Estas rutas corresponden al flujo de nodos de compatibilidad. Para operar el catálogo sísmico, usa las rutas `/events`.

## Carga de archivos y estado

La interfaz permite elegir archivos JSON locales mediante el selector del navegador. `POST /events/import-nodes` carga una lista de eventos y mantiene el orden de inserción en el AVL. `POST /events/import` recibe un respaldo del estado operativo con topología, datos, cola y parámetros.

El catálogo backend actual vive en memoria. Las versiones nombradas permanecen durante la sesión del servidor. Para conservarlas al cerrar, exporta el estado completo y vuelve a importarlo después. El módulo `src/services/eventCatalog/persistence.py` no está conectado al ciclo de vida activo del catálogo.

Las acciones que registran undo guardan snapshots del estado anterior, incluyendo la topología AVL, para permitir restaurarla. El costo de snapshots completos crece con el número de acciones y el tamaño del catálogo: aproximadamente `O(A × (E + Q + R))`, donde `A` es el número de acciones, `E` los eventos, `Q` los reportes en cola y `R` las referencias de asociación. Es una representación sencilla para escenarios académicos de tamaño moderado; catálogos grandes se beneficiarían de snapshots con copy-on-write o registros de cambios inversos.

## Casos mínimos del requerimiento 16

Los archivos están en `data/casos_minimos/`:

1. `16_1_limites_y_empates.json` — límites de prioridad, zona en el borde y desempate por identificador.
2. `16_2_correccion_reporte_antiguo.json` — corrección con cambio de prioridad y reporte de revisión menor.
3. `16_3_reporte_tardio.json` — eventos cercanos y procesamiento de un reporte tardío.
4. `16_4_rotaciones_recuperacion.json` — casos LL, RR, LR, RL y recuperación en estrés.
5. `16_5_archivo_masivo.json` — selección de rama elegible, casos sin elegibilidad y undo.
6. `16_6_persistencia_consistencia.json` — importación de topologías y versiones, consistencia y undo.

Los resultados marcados como calculados en estos archivos no son capturas de una ejecución del backend. El caso 16.6 requiere completar los objetos de evento con todos los campos obligatorios del esquema exportado antes de usarlo como archivo de importación.

## Pruebas

El repositorio incluye pruebas unitarias en `tests/`. Para ejecutarlas desde la raíz:

```powershell
python -m unittest discover -s tests -v
```

## Estado conocido del proyecto

Esta sección evita presentar como terminadas funciones cuya integración todavía está pendiente:

- Las rutas `/events/verify` y `/events/history` están declaradas, pero sus controladores llaman a métodos (`verify_structure` y `history_report`) que no están implementados actualmente en `EventCatalog`.
- El cálculo de asociaciones implementado no coincide todavía con la política de magnitud, ocurrencia anterior, ventana `W` y radio `R` descrita en el documento del proyecto.
- El catálogo devuelve actualmente un conjunto reducido de métricas; los contadores detallados de auditoría que esperan algunos componentes de Inicio aún no están conectados.
- La profundidad estructural del nodo usa raíz `1`; el requerimiento define raíz `0`. El límite de acceso costoso no está configurado como parámetro persistente `L` del escenario.
- La carga de estado valida parte de la topología, pero necesita validaciones adicionales de identidades globales, datos derivados y referencias de asociaciones.
- La importación de lotes de reportes exige identificadores únicos dentro del lote. Esto impide incluir en un mismo archivo varios reportes para un mismo evento.

## Licencia y uso académico

Proyecto desarrollado con fines educativos para estudiar árboles AVL/BST, estructuras lineales, validación, persistencia de estado y visualización de datos.
