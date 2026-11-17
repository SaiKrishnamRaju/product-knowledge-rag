from sqlalchemy import Text, cast, func, literal_column, select
from sqlalchemy.dialects.postgresql import TSQUERY

from app.db.models import Chunk, Document


def lexical_search(db, question, limit=20, product_model=None):
    # PostgreSQL quotes lexemes before replacing the AND operators it inserts.
    terms = func.plainto_tsquery(literal_column("'simple'::regconfig"), question)
    query = cast(func.replace(cast(terms, Text), " & ", " | "), TSQUERY)
    stmt = (select(Chunk).join(Document)
            .where(Chunk.search_vector.op("@@")(query))
            .order_by(func.ts_rank_cd(Chunk.search_vector, query).desc(), Chunk.id).limit(limit))
    if product_model:
        stmt = stmt.where(Document.product_model == product_model)
    return db.scalars(stmt).all()
