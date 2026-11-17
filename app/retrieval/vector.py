from sqlalchemy import select

from app.db.models import Chunk, Document


def vector_search(db, vector, limit=20, product_model=None):
    stmt = select(Chunk).join(Document).order_by(Chunk.embedding.cosine_distance(vector), Chunk.id).limit(limit)
    if product_model:
        stmt = stmt.where(Document.product_model == product_model)
    return db.scalars(stmt).all()
