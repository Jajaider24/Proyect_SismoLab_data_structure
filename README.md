# SismoLab AVL Proyecto de estructuras de datos

Presentado a: Jeferson Arango
Presentado por:
- Joaquin Hoyos
- Jaider León

## Descripción breve del proyecto

SismoLab AVL es una aplicación para gestionar un observatorio sísmico simulado. Su estructura central es un árbol AVL, utilizado para almacenar y consultar eventos sísmicos manteniendo el orden de sus claves y un balance eficiente después de inserciones y eliminaciones.

El proyecto hace parte de la asignatura de estructuras de datos y utiliza un territorio ficticio para representar eventos, estaciones, zonas y reportes sísmicos. Su propósito es demostrar el uso práctico de árboles binarios de búsqueda, árboles AVL, recorridos, rotaciones, alturas y factores de balance. Los datos y clasificaciones del simulador no representan predicciones ni evaluaciones reales de riesgo sísmico.

## Objetivos

- Implementar un árbol BST y un árbol AVL sin delegar sus operaciones a bibliotecas de árboles.
- Mantener el orden de los eventos mediante claves comparables.
- Aplicar correctamente las rotaciones LL, RR, LR y RL.
- Comparar el comportamiento estructural de un BST y un AVL.
- Proporcionar una base para gestionar eventos, reportes y consultas del observatorio.
- Exponer las operaciones principales mediante una API backend.

## Estructura del proyecto

```
.
├── main.py                         # Configuración principal de FastAPI
├── requirements.txt                # Dependencias del backend
├── data/                           # Datos de prueba y archivos de carga
├── docs/                           # Documentación técnica y de usuario
├── src/
│   ├── controllers/                # Lógica de entrada de las solicitudes
│   ├── core/
│   │   ├── AvlTree/                # Implementación del árbol AVL
│   │   ├── BstTree/                # Implementación del árbol BST
│   │   └── node/                   # Nodo compartido por las estructuras
│   ├── models/                     # Modelos del dominio sísmico
│   ├── routes/                     # Rutas HTTP de la API
│   └── services/                   # Servicios de aplicación
└── tests/                          # Pruebas automatizadas
```

## Requisitos previos

- Python 3.10 o una versión posterior.
- `pip` disponible en el entorno de Python.
- Node.js y npm únicamente si se desarrolla o ejecuta el frontend.

## Instalación

### 1. Crear el entorno virtual

    python -m venv venv

### 2. Activar el entorno virtual en Windows
    venv\Scripts\activate

### 3.instalar dependecias
backend:
    pip install -r requirements.txt

fronted:
    npm install


## Ejecución

Con el entorno virtual activado, iniciar el backend con:

```
uvicorn main:app --reload
```

El servidor estará disponible en:

```
http://127.0.0.1:8000
```

## Documentación de la API

FastAPI genera documentación interactiva automáticamente:

- Swagger UI: `http://127.0.0.1:8000/docs`
- ReDoc: `http://127.0.0.1:8000/redoc`
- Especificación OpenAPI: `http://127.0.0.1:8000/openapi.json`

## Rutas disponibles

### Insertar un valor en el AVL

```
POST /avl/insert/{value}
```
## Implementación de estructuras

El árbol AVL mantiene una altura de `-1` para un árbol vacío y de `0` para una hoja. El factor de balance se calcula así:

```
factor de balance = altura del subárbol izquierdo
                    - altura del subárbol derecho
```

Después de cada inserción o eliminación, el árbol actualiza las alturas y aplica las rotaciones necesarias para conservar factores de balance entre `-1` y `1`.

El BST se utiliza como estructura de comparación. Ambos árboles trabajan con la clase `Node`, que conserva el valor, el padre, los hijos izquierdo y derecho, y la altura del nodo.

## Estado actual

Actualmente se encuentra implementada la base estructural del proyecto:

- Nodo compartido.
- Árbol BST.
- Árbol AVL con inserción, eliminación, búsqueda, recorridos y rotaciones.
- Servicio de inserción AVL.
- API FastAPI básica.

Como trabajo pendiente del alcance completo de SismoLab se encuentran la interfaz gráfica, el procesamiento de reportes y revisiones, la cola de reportes, la pila de deshacer, el histórico, las asociaciones entre eventos, la persistencia JSON, las versiones y las métricas avanzadas.

## Propósito académico

El proyecto busca evidenciar cómo las estructuras de datos permiten organizar información, mantener invariantes y analizar costos de operación. Las decisiones de diseño deberán complementarse con pruebas, documentación técnica y demostraciones de los casos exigidos por el proyecto.
