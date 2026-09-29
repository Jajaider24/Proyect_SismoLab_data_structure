"""
Flight Management System Backend API.

This module initializes the FastAPI application for the Flight Management System,
configuring CORS middleware and registering all API route modules for flight operations,
tree management, versioning, and queue processing.
"""

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from src.routes.avl_routes import router as avl_router

# CORS origins allowed for frontend communication
cors_origins = [
    "http://localhost:5173",
    "http://localhost:5174",
    "http://127.0.0.1:5173",
    "http://127.0.0.1:5174",
]

# Initialize FastAPI application instance
app = FastAPI(
    title="Flight Management System API",
    description="API for AVL trees ",
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
