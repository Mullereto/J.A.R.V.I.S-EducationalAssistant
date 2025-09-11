import os
import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
import faiss
import json
from app.utils.logger import get_logger

logger = get_logger("embeddings_service")
EMBEDDING_MODEL = "BAAI/bge-large-en-v1.5"
INDEX_DIR = "data\\processed\\faiss"
INDEX_FILE = os.path.join(INDEX_DIR, "index.faiss")
META_FILE = os.path.join(INDEX_DIR, "meta.json")
EMBED_DIM = None  

# Load SentenceTransformer model once
logger.info("Loading embedding model %s", EMBEDDING_MODEL)
embed_model = SentenceTransformer(EMBEDDING_MODEL)
EMBED_DIM = embed_model.get_sentence_embedding_dimension()
logger.info("Embedding dimension: %d", EMBED_DIM)

_index = None
_metadata = {} # id -> metadata (text, source, chunk_id, etc.)

def _init_index():
    global _index, _metadata
    if _index is not None:
        return _index

    if os.path.exists(INDEX_FILE) and os.path.exists(META_FILE):
        try:
            logger.info("Loading FAISS index from %s", INDEX_FILE)
            _index = faiss.read_index(INDEX_FILE)
            with open(META_FILE, "r", encoding="utf-8") as f:
                _metadata = json.load(f)
            return _index
        except Exception as e:
            logger.warning("Failed to load existing index: %s. Creating new index.", e)
    
    logger.info("Creating new FAISS index (IndexFlatIP)")
    _index = faiss.IndexFlatIP(EMBED_DIM)
    _metadata = {}
    return _index

def _save_index():
    global _index, _metadata
    if _index is None:
        return
    try:
        faiss.write_index(_index, INDEX_FILE)
        with open(META_FILE, "w", encoding="utf-8") as f:
            json.dump(_metadata, f, ensure_ascii=False, indent=2)
        logger.info("Saved FAISS index and metadata")
    except Exception as e:
        logger.warning("Failed to save index: %s", e)

def embed_texts(texts: List[str]) -> List[np.ndarray]:
    """Return L2-normalized embeddings for a list of texts."""
    #logger.info(f"Loaded HuggingFace model: {os.getenv('HF_MODEL_NAME', 'all-MiniLM-L6-v2')}")
    embeddings = embed_model.encode(texts, convert_to_numpy=True, show_progress_bar=False)
    norms = np.linalg.norm(embeddings, axis=1, keepdims=True)
    norms[norms == 0] = 1.0
    embeddings = embeddings / norms
    return embeddings


def add_documents(docs: List[Dict[str, Any]]) -> List[str]:
    """
    Add docs: each doc = {'id': str, 'text': str, 'source': str, 'meta': {...}}
    Returns list of doc ids added.
    """    
    global _index, _metadata
    _init_index()
    texts = [d["text"] for d in docs]
    ids = [d["id"] for d in docs]
    
    embeds = embed_texts(texts=texts)
    start_idx = _index.ntotal
    _index.add(embeds)
    for i, id in enumerate(ids):
        _metadata[id] = docs[i]

    _save_index()
    logger.info("Added %d documents to index", len(docs))
    return ids
