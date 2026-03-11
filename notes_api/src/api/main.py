"""
NoteMaster Pro API - Main FastAPI application entry point.
Provides endpoints for notes management, authentication, tags, and folders.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from dotenv import load_dotenv

from .database import engine, Base
from .routers import auth, notes, tags, folders

load_dotenv()

# Initialize database tables
Base.metadata.create_all(bind=engine)

# Get allowed origins from environment
ALLOWED_ORIGINS = os.getenv(
    "ALLOWED_ORIGINS",
    "http://localhost:3000,https://vscode-internal-13696-uat.uat01.cloud.kavia.ai:3000"
).split(",")

# Create FastAPI app with OpenAPI metadata
app = FastAPI(
    title="NoteMaster Pro API",
    description="""
    ## NoteMaster Pro Backend API

    A comprehensive notes management API supporting:
    - **Authentication**: JWT-based user registration and login
    - **Notes**: Full CRUD with markdown content, autosave
    - **Tags**: Color-coded tags for note categorization
    - **Folders**: Hierarchical note organization
    - **Search**: Full-text search across notes
    - **Filtering**: Filter by pinned, favorite, archived status
    """,
    version="1.0.0",
    openapi_tags=[
        {"name": "Authentication", "description": "User registration, login, and profile"},
        {"name": "Notes", "description": "Note CRUD, search, pin/favorite/archive"},
        {"name": "Tags", "description": "Tag management for note organization"},
        {"name": "Folders", "description": "Folder management for note organization"},
    ]
)

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS + ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(auth.router)
app.include_router(notes.router)
app.include_router(tags.router)
app.include_router(folders.router)


@app.get("/", tags=["Health"], summary="Health check", description="Check if the API is running.")
def health_check():
    """
    Health check endpoint.

    Returns:
        Status message indicating API is healthy
    """
    return {"message": "NoteMaster Pro API is healthy", "version": "1.0.0"}
