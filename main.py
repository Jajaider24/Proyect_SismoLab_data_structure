"""Aplicacion FastAPI para el observatorio de eventos sismicos SismoLab."""

import logging

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from src.routes.avl_routes import router as avl_router
from src.routes.event_routes import router as event_router

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s | %(levelname)s | %(name)s | %(message)s",
)

# CORS origins allowed for frontend communication
cors_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Initialize FastAPI application instance
app = FastAPI(
    title="SismoLab API",
    description="API para el catálogo de eventos sísmicos y su índice AVL.",
    version="1.0.0"
)

# Configure CORS middleware for cross-origin requests
app.add_middleware(
    CORSMiddleware,
    allow_origins=cors_origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(avl_router)
app.include_router(event_router)


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    """Registra y normaliza errores de parametros detectados por FastAPI."""
    logging.getLogger(__name__).warning(
        "[422] Solicitud invalida %s %s: %s", request.method, request.url.path, exc.errors()
    )
    return JSONResponse(
        status_code=422,
        content={"status_code": 422, "message": "La solicitud contiene datos invalidos.",
                 "errors": exc.errors()},
    )
