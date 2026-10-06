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
- `POST /events/reports/process/step` procesa exactamente un reporte FIFO.
- `POST /events/reports/process` procesa la cola FIFO de reportes pendientes.
- `POST /events/undo` deshace la ultima accion.
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

## Pruebas

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```
