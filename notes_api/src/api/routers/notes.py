"""
Notes router for NoteMaster Pro API.
Handles CRUD operations for notes, including search, pin/favorite, autosave.
"""
import uuid
from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.orm import Session
from sqlalchemy import or_

from .. import models, schemas
from ..database import get_db
from ..auth import get_current_user

router = APIRouter(prefix="/notes", tags=["Notes"])


# PUBLIC_INTERFACE
@router.post("/", response_model=schemas.NoteResponse, status_code=status.HTTP_201_CREATED,
             summary="Create a new note",
             description="Create a new note with optional title, content, folder, and tags.")
def create_note(
    note_data: schemas.NoteCreate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Create a new note for the authenticated user.

    Args:
        note_data: Note creation data including title, content, folder_id, tag_ids
        db: Database session
        current_user: Authenticated user

    Returns:
        The created note with all relationships populated
    """
    # Validate folder belongs to user
    folder = None
    if note_data.folder_id:
        folder = db.query(models.Folder).filter(
            models.Folder.id == note_data.folder_id,
            models.Folder.user_id == current_user.id
        ).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

    # Create the note
    note = models.Note(
        title=note_data.title,
        content=note_data.content,
        is_pinned=note_data.is_pinned,
        is_favorite=note_data.is_favorite,
        folder_id=note_data.folder_id,
        user_id=current_user.id
    )
    db.add(note)
    db.flush()

    # Assign tags
    if note_data.tag_ids:
        tags = db.query(models.Tag).filter(
            models.Tag.id.in_(note_data.tag_ids),
            models.Tag.user_id == current_user.id
        ).all()
        note.tags = tags

    db.commit()
    db.refresh(note)
    return note


# PUBLIC_INTERFACE
@router.get("/", response_model=schemas.NoteListResponse,
            summary="List notes",
            description="List notes with optional filtering by search, folder, tag, pinned, favorite status.")
def list_notes(
    search: Optional[str] = Query(None, description="Search in title and content"),
    folder_id: Optional[uuid.UUID] = Query(None, description="Filter by folder ID"),
    tag_id: Optional[uuid.UUID] = Query(None, description="Filter by tag ID"),
    is_pinned: Optional[bool] = Query(None, description="Filter by pinned status"),
    is_favorite: Optional[bool] = Query(None, description="Filter by favorite status"),
    is_archived: Optional[bool] = Query(False, description="Filter by archived status"),
    page: int = Query(1, ge=1, description="Page number"),
    page_size: int = Query(20, ge=1, le=100, description="Items per page"),
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    List notes for the authenticated user with filtering and pagination.

    Args:
        search: Optional text search in title and content
        folder_id: Optional folder filter
        tag_id: Optional tag filter
        is_pinned: Optional pinned filter
        is_favorite: Optional favorite filter
        is_archived: Archived filter (default False)
        page: Page number for pagination
        page_size: Number of items per page
        db: Database session
        current_user: Authenticated user

    Returns:
        Paginated list of notes with total count
    """
    query = db.query(models.Note).filter(models.Note.user_id == current_user.id)

    # Apply filters
    if is_archived is not None:
        query = query.filter(models.Note.is_archived == is_archived)
    if search:
        query = query.filter(
            or_(
                models.Note.title.ilike(f"%{search}%"),
                models.Note.content.ilike(f"%{search}%")
            )
        )
    if folder_id:
        query = query.filter(models.Note.folder_id == folder_id)
    if tag_id:
        query = query.filter(models.Note.tags.any(models.Tag.id == tag_id))
    if is_pinned is not None:
        query = query.filter(models.Note.is_pinned == is_pinned)
    if is_favorite is not None:
        query = query.filter(models.Note.is_favorite == is_favorite)

    # Order: pinned first, then by updated_at
    query = query.order_by(
        models.Note.is_pinned.desc(),
        models.Note.updated_at.desc()
    )

    total = query.count()
    notes = query.offset((page - 1) * page_size).limit(page_size).all()

    return schemas.NoteListResponse(
        notes=notes,
        total=total,
        page=page,
        page_size=page_size
    )


# PUBLIC_INTERFACE
@router.get("/{note_id}", response_model=schemas.NoteResponse,
            summary="Get a note",
            description="Retrieve a single note by ID.")
def get_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Get a single note by ID for the authenticated user.

    Args:
        note_id: UUID of the note to retrieve
        db: Database session
        current_user: Authenticated user

    Returns:
        The note with all relationships

    Raises:
        HTTPException 404 if note not found
    """
    note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    return note


# PUBLIC_INTERFACE
@router.put("/{note_id}", response_model=schemas.NoteResponse,
            summary="Update a note",
            description="Update a note's title, content, folder, tags, or status flags.")
def update_note(
    note_id: uuid.UUID,
    note_data: schemas.NoteUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Update a note by ID for the authenticated user.

    Args:
        note_id: UUID of the note to update
        note_data: Fields to update (all optional)
        db: Database session
        current_user: Authenticated user

    Returns:
        The updated note

    Raises:
        HTTPException 404 if note not found
    """
    note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    # Update fields if provided
    update_data = note_data.model_dump(exclude_unset=True)

    # Handle tag_ids separately
    tag_ids = update_data.pop("tag_ids", None)

    # Handle folder_id validation
    if "folder_id" in update_data and update_data["folder_id"]:
        folder = db.query(models.Folder).filter(
            models.Folder.id == update_data["folder_id"],
            models.Folder.user_id == current_user.id
        ).first()
        if not folder:
            raise HTTPException(status_code=404, detail="Folder not found")

    for field, value in update_data.items():
        setattr(note, field, value)

    if tag_ids is not None:
        tags = db.query(models.Tag).filter(
            models.Tag.id.in_(tag_ids),
            models.Tag.user_id == current_user.id
        ).all()
        note.tags = tags

    db.commit()
    db.refresh(note)
    return note


# PUBLIC_INTERFACE
@router.delete("/{note_id}", status_code=status.HTTP_204_NO_CONTENT,
               summary="Delete a note",
               description="Permanently delete a note by ID.")
def delete_note(
    note_id: uuid.UUID,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Delete a note by ID for the authenticated user.

    Args:
        note_id: UUID of the note to delete
        db: Database session
        current_user: Authenticated user

    Raises:
        HTTPException 404 if note not found
    """
    note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")
    db.delete(note)
    db.commit()


# PUBLIC_INTERFACE
@router.patch("/{note_id}/autosave", response_model=schemas.NoteResponse,
              summary="Autosave note",
              description="Save note content and title during editing (lightweight update).")
def autosave_note(
    note_id: uuid.UUID,
    note_data: schemas.NoteUpdate,
    db: Session = Depends(get_db),
    current_user: models.User = Depends(get_current_user)
):
    """
    Autosave endpoint for continuous note editing.
    Only updates title and content fields.

    Args:
        note_id: UUID of the note
        note_data: Partial update with title and/or content
        db: Database session
        current_user: Authenticated user

    Returns:
        The updated note

    Raises:
        HTTPException 404 if note not found
    """
    note = db.query(models.Note).filter(
        models.Note.id == note_id,
        models.Note.user_id == current_user.id
    ).first()
    if not note:
        raise HTTPException(status_code=404, detail="Note not found")

    if note_data.title is not None:
        note.title = note_data.title
    if note_data.content is not None:
        note.content = note_data.content

    db.commit()
    db.refresh(note)
    return note
