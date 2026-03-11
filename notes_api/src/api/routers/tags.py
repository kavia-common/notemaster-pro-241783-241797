"""
Tags router for NoteMaster Pro API.
Handles CRUD operations for tags.
"""
import uuid
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/tags", tags=["Tags"])


# PUBLIC_INTERFACE
@router.post("/", response_model=schemas.TagResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a tag",
             description="Create a new tag for organizing notes.")
def create_tag(
    tag_data: schemas.TagCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new tag.

    Args:
        tag_data: Tag name and color
        db: Database session
        current_user: Authenticated user

    Returns:
        The created tag

    Raises:
        HTTPException 400 if tag name already exists for user
    """
    existing = db.query(models.Tag).filter(
        models.Tag.name == tag_data.name,
        models.Tag.user_id == current_user.id
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="Tag with this name already exists")

    tag = models.Tag(
        name=tag_data.name,
        color=tag_data.color,
        user_id=current_user.id
    )
    db.add(tag)
    db.commit()
    db.refresh(tag)
    return tag


# PUBLIC_INTERFACE
@router.get("/", response_model=List[schemas.TagResponse],
            summary="List tags",
            description="List all tags for the authenticated user.")
def list_tags(
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List all tags for the authenticated user.

    Args:
        db: Database session
        current_user: Authenticated user

    Returns:
        List of all user's tags
    """
    return db.query(models.Tag).filter(
        models.Tag.user_id == current_user.id
    ).order_by(models.Tag.name).all()


# PUBLIC_INTERFACE
@router.put("/{tag_id}", response_model=schemas.TagResponse,
            summary="Update a tag",
            description="Update a tag's name or color.")
def update_tag(
    tag_id: uuid.UUID,
    tag_data: schemas.TagUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update a tag by ID.

    Args:
        tag_id: UUID of the tag to update
        tag_data: Fields to update
        db: Database session
        current_user: Authenticated user

    Returns:
        The updated tag

    Raises:
        HTTPException 404 if tag not found
    """
    tag = db.query(models.Tag).filter(
        models.Tag.id == tag_id,
        models.Tag.user_id == current_user.id
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")

    update_data = tag_data.model_dump(exclude_unset=True)
    for field, value in update_data.items():
        setattr(tag, field, value)

    db.commit()
    db.refresh(tag)
    return tag


# PUBLIC_INTERFACE
@router.delete("/{tag_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a tag",
               description="Delete a tag by ID.")
def delete_tag(
    tag_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a tag by ID.

    Args:
        tag_id: UUID of the tag to delete
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404 if tag not found
    """
    tag = db.query(models.Tag).filter(
        models.Tag.id == tag_id,
        models.Tag.user_id == current_user.id
    ).first()
    if not tag:
        raise HTTPException(status_code=404, detail="Tag not found")
    db.delete(tag)
    db.commit()
