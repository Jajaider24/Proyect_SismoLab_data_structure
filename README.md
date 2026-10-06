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

## UI

Con el backend ejecutandose, abre otra terminal y sirve la carpeta estatica:

```powershell
python -m http.server 5173 --directory UI
```

Luego visita `http://localhost:5173`. La UI esta separada en API, servicio,
renderizador D3 y aplicacion, y usa el CDN de D3.js. El catalogo mantiene un
indice auxiliar por identificador y separa el estado activo del historico.
Las coordenadas del escenario son `x` e `y` en el rango `0..1000` km.

## Pruebas

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```
