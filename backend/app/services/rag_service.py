"""
RAG retrieval service — queries the FAISS vector store for relevant
knowledge-base chunks and returns them as a single context string.
"""

from app.database.vector_store import get_vector_store
from app.utils.config import RAG_TOP_K
from app.utils.logger import logger


def retrieve_context(query: str) -> str:
    """
    Perform a similarity search against the FAISS index and return the
    concatenated page contents of the top-k results.

    Returns an empty string if the vector store has not been loaded.
    """
    store = get_vector_store()
    if store is None:
        logger.warning("Vector store not loaded — returning empty context.")
        return ""

    try:
        docs = store.similarity_search(query, k=RAG_TOP_K)
        context_parts = [doc.page_content for doc in docs]
        context = "\n\n---\n\n".join(context_parts)
        logger.info(
            "RAG retrieved %d chunks (total %d chars) for query: '%.80s…'",
            len(docs),
            len(context),
            query,
        )
        return context
    except Exception as exc:
        logger.error("RAG retrieval failed: %s", exc, exc_info=True)
        return ""
