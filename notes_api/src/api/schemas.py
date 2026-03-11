"""
Pydantic schemas for NoteMaster Pro API request/response validation.
Defines schemas for users, notes, tags, folders, and authentication.
"""
import uuid
from datetime import datetime
from typing import Optional, List
from pydantic import BaseModel, EmailStr, Field


# ─── Auth Schemas ────────────────────────────────────────────────────────────

class UserRegister(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="Password (min 6 characters)")


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username or email")
    password: str = Field(..., description="User password")


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(default="bearer", description="Token type")


class UserResponse(BaseModel):
    """Schema for user data response."""
    id: uuid.UUID
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Tag Schemas ─────────────────────────────────────────────────────────────

class TagCreate(BaseModel):
    """Schema for creating a tag."""
    name: str = Field(..., min_length=1, max_length=50, description="Tag name")
    color: str = Field(default="#06b6d4", description="Tag color hex code")


class TagUpdate(BaseModel):
    """Schema for updating a tag."""
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    color: Optional[str] = None


class TagResponse(BaseModel):
    """Schema for tag data response."""
    id: uuid.UUID
    name: str
    color: str
    created_at: datetime

    class Config:
        from_attributes = True


# ─── Folder Schemas ───────────────────────────────────────────────────────────

class FolderCreate(BaseModel):
    """Schema for creating a folder."""
    name: str = Field(..., min_length=1, max_length=100, description="Folder name")
    color: str = Field(default="#3b82f6", description="Folder color hex code")


class FolderUpdate(BaseModel):
    """Schema for updating a folder."""
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    color: Optional[str] = None


class FolderResponse(BaseModel):
    """Schema for folder data response."""
    id: uuid.UUID
    name: str
    color: str
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


# ─── Note Schemas ─────────────────────────────────────────────────────────────

class NoteCreate(BaseModel):
    """Schema for creating a note."""
    title: str = Field(default="Untitled Note", max_length=255, description="Note title")
    content: str = Field(default="", description="Note content (supports markdown)")
    is_pinned: bool = Field(default=False, description="Whether the note is pinned")
    is_favorite: bool = Field(default=False, description="Whether the note is favorited")
    folder_id: Optional[uuid.UUID] = Field(None, description="Folder ID to organize the note")
    tag_ids: List[uuid.UUID] = Field(default=[], description="List of tag IDs to assign")


class NoteUpdate(BaseModel):
    """Schema for updating a note (all fields optional)."""
    title: Optional[str] = Field(None, max_length=255)
    content: Optional[str] = None
    is_pinned: Optional[bool] = None
    is_favorite: Optional[bool] = None
    is_archived: Optional[bool] = None
    folder_id: Optional[uuid.UUID] = None
    tag_ids: Optional[List[uuid.UUID]] = None


class NoteResponse(BaseModel):
    """Schema for note data response."""
    id: uuid.UUID
    title: str
    content: str
    is_pinned: bool
    is_favorite: bool
    is_archived: bool
    folder_id: Optional[uuid.UUID]
    folder: Optional[FolderResponse]
    tags: List[TagResponse]
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class NoteListResponse(BaseModel):
    """Schema for paginated note list response."""
    notes: List[NoteResponse]
    total: int
    page: int
    page_size: int
