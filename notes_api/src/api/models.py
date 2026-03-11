"""
SQLAlchemy ORM models for NoteMaster Pro.
Defines User, Note, Tag, Folder, and association tables.
"""
import uuid
from datetime import datetime
from sqlalchemy import (
    Column, String, Text, Boolean, DateTime, ForeignKey, Table, Integer
)
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from .database import Base

# Association table for Note <-> Tag many-to-many relationship
note_tags = Table(
    "note_tags",
    Base.metadata,
    Column("note_id", UUID(as_uuid=True), ForeignKey("notes.id", ondelete="CASCADE"), primary_key=True),
    Column("tag_id", UUID(as_uuid=True), ForeignKey("tags.id", ondelete="CASCADE"), primary_key=True),
)


class User(Base):
    """Represents an application user with authentication credentials."""
    __tablename__ = "users"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    notes = relationship("Note", back_populates="owner", cascade="all, delete-orphan")
    tags = relationship("Tag", back_populates="owner", cascade="all, delete-orphan")
    folders = relationship("Folder", back_populates="owner", cascade="all, delete-orphan")


class Folder(Base):
    """Represents a folder for organizing notes."""
    __tablename__ = "folders"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(100), nullable=False)
    color = Column(String(20), default="#3b82f6")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="folders")
    notes = relationship("Note", back_populates="folder")


class Tag(Base):
    """Represents a tag for categorizing notes."""
    __tablename__ = "tags"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    name = Column(String(50), nullable=False)
    color = Column(String(20), default="#06b6d4")
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="tags")
    notes = relationship("Note", secondary=note_tags, back_populates="tags")


class Note(Base):
    """Represents a note with content, metadata, and relationships."""
    __tablename__ = "notes"

    id = Column(UUID(as_uuid=True), primary_key=True, default=uuid.uuid4)
    title = Column(String(255), nullable=False, default="Untitled Note")
    content = Column(Text, default="")
    is_pinned = Column(Boolean, default=False)
    is_favorite = Column(Boolean, default=False)
    is_archived = Column(Boolean, default=False)
    folder_id = Column(UUID(as_uuid=True), ForeignKey("folders.id", ondelete="SET NULL"), nullable=True)
    user_id = Column(UUID(as_uuid=True), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)

    # Relationships
    owner = relationship("User", back_populates="notes")
    folder = relationship("Folder", back_populates="notes")
    tags = relationship("Tag", secondary=note_tags, back_populates="notes")
