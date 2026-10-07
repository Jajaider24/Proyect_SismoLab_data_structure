## Backend

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

La API AVL original conserva `POST /avl/insert/{value}`, `GET /avl/tree` y
`DELETE /avl/tree` para compatibilidad. El flujo de eventos usa `/events`:

- `POST /events` crea un evento completo.
- `POST /events/import-nodes` recibe una lista JSON de nodos y valida los IDs
  antes de insertarlos uno por uno en el AVL activo. Cada objeto debe incluir
  `id` entero único; también se aceptan `identifier` e `identificador`.
  Los campos opcionales aceptan nombres ingleses o los equivalentes
  `magnitud`, `profundidad_h`, `fecha_hora` y `procedencia`. Si se omiten,
  magnitud, profundidad y coordenadas comienzan en cero, la fecha usa el reloj
  de simulación y la procedencia queda como `IMPORTACION_JSON`. El lote se
  registra como una única acción de undo y se rechaza completo si un ID ya
  existe o algún nodo no es válido.
- `GET /events/{identifier}` consulta eventos activos, archivados o eliminados.
- `PUT /events/{identifier}` corrige un evento y genera la revision siguiente.
- `POST /events/{identifier}/review` cambia solo el estado de atencion.
- `DELETE /events/{identifier}` elimina individualmente y conserva el historico.
- `POST /events/{identifier}/archive` archiva la rama seleccionada.
- `POST /events/archive/old/preview` selecciona una rama cuyos eventos son de
  prioridad baja y superan la antigüedad mínima (72 horas por defecto); acepta
  `threshold_hours` para configurar el umbral. La interfaz muestra la lista,
  el tamaño y el motivo antes de permitir confirmar el archivo.
- `POST /events/archive/old` ejecuta el archivo confirmado usando
  `threshold_hours` y `expected_identifiers`; si el árbol cambió desde la
  previsualización, la operación se rechaza sin modificar el catálogo. El
  archivo completo se deshace con una sola acción.
- `POST /events/reports` procesa reportes por revision.
- `POST /events/reports/import` valida una lista JSON de reportes y la agrega
  completa al final de la cola FIFO en orden de archivo, sin procesarla. Cada
  reporte debe tener un ID entero único dentro del archivo y cumplir las mismas
  reglas de datos que un reporte individual; una carga inválida no encola nada.
- `POST /events/reports/process/step` procesa exactamente un reporte FIFO.
- `POST /events/reports/process` procesa la cola FIFO de reportes pendientes.
- `POST /events/undo` deshace la ultima accion.
- `GET /events/history` informa cuantas acciones quedan en la pila.
- `GET /events/verify` comprueba orden global por K, unicidad, referencias,
  enlaces, alturas y balance y devuelve inconsistencias por identificador.
- `GET /events/scenario` consulta reloj, parametros, modo y metricas.
- `PUT /events/scenario/parameters` cambia el umbral de archivo o las zonas
  pobladas; cada cambio confirmado se registra como una accion.
- `POST /events/clock/advance` avanza el reloj de simulacion en segundos.
- `GET /events/export` exporta el estado operativo actual.
- `POST /events/import` carga una exportacion y deja la carga en la pila undo.
- `GET /events/versions`, `POST /events/versions` y
  `POST /events/versions/{name}/restore` administran versiones nombradas.
- `DELETE /events/versions/{name}` elimina una version guardada.
- `GET /events/tree` entrega el AVL, metricas y valores in-order.
- `GET /events/analysis/pending?k=5` devuelve hasta k pendientes en orden
  descendente de `EventKey` (prioridad, magnitud, identificador).
- `GET /events/analysis/magnitude?minimum=3&maximum=6` y
  `GET /events/analysis/depth?maximum_depth=100&start=...&end=...` consultan
  rangos inclusivos.
- `GET /events/analysis/associations/{identifier}` devuelve candidatos, evento
  de referencia, asociados activos/archivados y nodos AVL examinados.
- `GET /events/analysis/costly-high-priority?depth_limit=2` lista eventos P3
  más profundos que el límite y cuenta las visitas de cada búsqueda por clave.
- `GET /events/analysis/compare` compara AVL y BST sobre las mismas claves
  activas, en orden de catálogo, ascendente y descendente.

Las consultas informan `nodes_examined` del AVL. El top-k recorre en orden
descendente y se detiene cuando encuentra k pendientes: por el orden inverso
al in-order, las claves restantes no pueden desplazar esos resultados. No hay
contadores auxiliares de pendientes por subárbol, así que antes de reunir k
puede revisar todo el árbol (O(n)); usa una pila O(h). Magnitud y profundidad/
fecha también son O(n), ya que no son intervalos contiguos de la clave
compuesta; su pila ocupa O(h). En la consulta P3 se puede descartar el hijo
izquierdo de un nodo P1/P2: prioridad es el primer componente de K. El peor
caso para seleccionar candidatos sigue siendo O(n). Cada búsqueda de un P3
profundo cuesta O(h), por lo que la consulta completa puede costar O(nh),
O(n log n) con un AVL equilibrado y O(n²) en modo de estrés. Asociaciones usa
los conjuntos del catálogo activo e histórico, examina 0 nodos AVL y recorre
O(n) eventos para localizar quiénes incluyen la referencia; la copia temporal
de los diccionarios también usa O(n) memoria. No existe un índice auxiliar
direccional de referencias; el modelo actual guarda asociaciones mutuas.

La comparación reconstruye AVL y BST para cada orden y conserva O(n) nodos;
calcular altura/hojas cuesta O(n). Las búsquedas cuestan O(n log n) en AVL y
hasta O(n²) en BST. La construcción ordenada del BST también es O(n²); la pila
iterativa para sus métricas usa O(h) memoria. Estas métricas estructurales
permiten ver el efecto del orden sin depender de tiempos de ejecución.

## UI

Con el backend ejecutandose, abre otra terminal y sirve la carpeta estatica:

```powershell
python -m http.server 5173 --directory UI
```

Luego visita `http://localhost:5173`. La interfaz organiza las funciones en
vistas independientes: resumen (`#inicio`), gestión de eventos (`#eventos`),
reportes (`#reportes`) y análisis (`#analisis`). La navegación conserva la vista
en el hash de la URL. La UI separa API, servicio, estado, componentes y
renderizador D3, y usa el CDN de D3.js. El catálogo mantiene un índice auxiliar
por identificador y separa el estado activo del histórico. Las coordenadas del
escenario son `x` e `y` en el rango `0..1000` km.

## Estado, versiones manuales y deshacer

El catalogo comienza vacio en cada ejecucion: no lee ni escribe automaticamente
`data/sismolab-state.json`. El usuario guarda versiones desde Inicio; estas se
mantienen en memoria durante la sesion. «Exportar estado completo» descarga un
JSON con el estado operativo, el historial undo y las versiones guardadas.
«Cargar un estado exportado» importa el archivo solo cuando el usuario lo elige;
la carga puede deshacerse. Las versiones se conservan al exportar e importar el
respaldo completo.

Cada paso FIFO genera su propia accion, incluso si el reporte se descarta; la
pila guarda una copia aislada de los datos, cola, reloj, parametros, modo y
enlaces izquierda/derecha del AVL. Por eso undo restaura la topologia previa en
vez de reconstruir una forma equivalente.

El historial usa snapshots completos para mantener sencilla la restauracion
exacta: con `A` acciones, `E` eventos, `Q` reportes pendientes y `R` referencias
de asociacion, el coste retenido es `O(A * (E + Q + R))`. Las copias se hacen
antes de cada accion y contienen solo objetos del estado operativo; las
rotaciones internas no generan snapshots. Las versiones añaden `O(V * (E + Q +
R))` para `V` versiones guardadas. Esta representacion favorece la claridad y la
exactitud para escenarios de simulacion de tamaño moderado; catálogos grandes
requeririan reemplazar los snapshots completos por cambios inversos o snapshots
con copy-on-write.

## Auditoría e indicadores

Inicio muestra eventos activos e históricos, altura (vacío -1, hoja 0), hojas,
prioridades, pendientes, correcciones aceptadas, descartes, conflictos, archivos
masivos y rotaciones. También expone recorridos inorden, preorden, postorden y
por niveles. LR/RL cuentan como un caso doble y dos giros elementales. El acceso
costoso se define como evento P3 a profundidad mayor que 2, el límite por defecto
de la consulta de costo.

**Verificar estructura** está en Reportes y funciona en ambos modos. Revisa los
límites globales de K, unicidad, referencias, enlaces, alturas y balance; en modo
estrés separa el desbalance esperado de los errores de orden o metadatos.
`GET /events/history` explica métricas anteriores y posteriores por acción. Los
contadores pertenecen a cada snapshot, por lo que undo y restauración recuperan
sus valores.

## Pruebas

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```
