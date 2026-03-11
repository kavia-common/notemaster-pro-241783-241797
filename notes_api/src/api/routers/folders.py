"""
Folders router for NoteMaster Pro API.
Handles CRUD operations for folders.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/folders", tags=["Folders"])


# PUBLIC_INTERFACE
@router.post("/", response_model=schemas.FolderResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a folder",
             description="Create a new folder for organizing notes.")
def create_folder(
    folder_data: schemas.FolderCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new folder.

    Args:
        folder_data: Folder name and color
        db: Database session
        current_user: Authenticated user

    Returns:
        The created folder

    Raises:
        HTTPException 400 if folder name already exists for user
    """
    existing = db.query(models.Folder).filter(
        models.Folder.name == folder_data.name,
        models.Folder.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Folder with this name already exists")

    folder = models.Folder(
        name=folder_data.name,
        color=folder_data.color,
        user_id=current_user.id
    )
    db.add(folder)
    db.commit()
    db.refresh(folder)
    return folder


# PUBLIC_INTERFACE
@router.get("/", response_model=List[schemas.FolderResponse],
            summary="List folders",
            description="List all folders for the authenticated user.")
def list_folders(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all folders for the authenticated user.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of all user's folders
    """
    return db.query(models.Folder).filter(
        models.Folder.user_id == current_user.id
    ).order_by(models.Folder.name).all()


# PUBLIC_INTERFACE
@router.put("/{folder_id}", response_model=schemas.FolderResponse,
            summary="Update a folder",
            description="Update a folder's name or color.")
def update_folder(
    folder_id: uuid.UUID,
    folder_data: schemas.FolderUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update a folder by ID.

    Args:
        folder_id: UUID of the folder to update
        folder_data: Fields to update
        db: Database session
        current_user: Authenticated user

    Returns:
        The updated folder

    Raises:
        HTTPException 404 if folder not found
    """
    folder = db.query(models.Folder).filter(
        models.Folder.id == folder_id,
        models.Folder.user_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")

    update_data = folder_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(folder, field, value)

    db.commit()
    db.refresh(folder)
    return folder


# PUBLIC_INTERFACE
@router.delete("/{folder_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a folder",
               description="Delete a folder by ID. Notes in the folder will be unassigned.")
def delete_folder(
    folder_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a folder by ID.

    Args:
        folder_id: UUID of the folder to delete
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404 if folder not found
    """
    folder = db.query(models.Folder).filter(
        models.Folder.id == folder_id,
        models.Folder.user_id == current_user.id
    ).first()
    if not folder:
        raise HTTPException(status_code=404, detail="Folder not found")
    db.delete(folder)
    db.commit()
