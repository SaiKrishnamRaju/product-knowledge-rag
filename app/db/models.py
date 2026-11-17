import uuid
from datetime import UTC, datetime

from pgvector.sqlalchemy import Vector
from sqlalchemy import Computed, DateTime, ForeignKey, Index, Integer, String, Text
from sqlalchemy.dialects.postgresql import TSVECTOR, UUID
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


class Base(DeclarativeBase):
    pass

def uid():
    return uuid.uuid4()

def now():
    return datetime.now(UTC)

class Document(Base):
    __tablename__ = "documents"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    title: Mapped[str] = mapped_column(Text)
    manufacturer: Mapped[str] = mapped_column(Text, default="")
    product_model: Mapped[str] = mapped_column(Text, default="", index=True)
    source_url: Mapped[str] = mapped_column(Text)
    sha256: Mapped[str] = mapped_column(String(64), unique=True)
    page_count: Mapped[int] = mapped_column(Integer)
    status: Mapped[str] = mapped_column(String(24), default="indexed")
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
    chunks: Mapped[list["Chunk"]] = relationship(back_populates="document", cascade="all, delete-orphan")

class Chunk(Base):
    __tablename__ = "chunks"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    document_id: Mapped[uuid.UUID] = mapped_column(ForeignKey("documents.id", ondelete="CASCADE"), index=True)
    page_number: Mapped[int] = mapped_column(Integer)
    chunk_index: Mapped[int] = mapped_column(Integer)
    content: Mapped[str] = mapped_column(Text)
    embedding = mapped_column(Vector(384), nullable=False)
    search_vector = mapped_column(TSVECTOR, Computed("to_tsvector('simple', content)", persisted=True))
    token_count: Mapped[int] = mapped_column(Integer)
    content_hash: Mapped[str] = mapped_column(String(64))
    document: Mapped[Document] = relationship(back_populates="chunks")
    __table_args__ = (Index("ix_chunks_search", "search_vector", postgresql_using="gin"),)

class QueryLog(Base):
    __tablename__ = "query_logs"
    id: Mapped[uuid.UUID] = mapped_column(UUID(as_uuid=True), primary_key=True, default=uid)
    question: Mapped[str] = mapped_column(Text)
    retrieval_mode: Mapped[str] = mapped_column(String(32))
    answer_status: Mapped[str] = mapped_column(String(20))
    latency_ms: Mapped[int] = mapped_column(Integer)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), default=now)
