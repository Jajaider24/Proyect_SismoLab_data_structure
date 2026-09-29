1. Crear un entorno virtual para el backend
    python -m venv venv
2. Iniciar el entorno virtual
    venv\Scripts\activate
3.instalar dependecias
    backend: pip install -r requirements.txt
    frontend: npm install
4. correr el proyecto
    backend :uvicorn main:app --reload