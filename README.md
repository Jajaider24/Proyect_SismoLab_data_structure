## Backend

```powershell
python -m venv venv
venv\Scripts\activate
pip install -r requirements.txt
uvicorn main:app --reload
```

La API AVL expone `POST /avl/insert/{value}`, `GET /avl/tree` y
`DELETE /avl/tree`. La respuesta incluye el recorrido in-order y un arbol
jerarquico con altura y factor de balance para la UI.

## UI

Con el backend ejecutandose, abre otra terminal y sirve la carpeta estatica:

```powershell
python -m http.server 5173 --directory ui
```

Luego visita `http://localhost:5173`. La UI esta separada en API, servicio,
renderizador D3 y aplicacion, y usa el CDN de D3.js.

## Pruebas

```powershell
venv\Scripts\python.exe -m unittest discover -s tests -v
```
