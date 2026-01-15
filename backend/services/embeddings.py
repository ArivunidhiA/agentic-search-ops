"""Vector embedding service for semantic search."""

import logging
import json
from typing import List, Optional
import asyncio

from core.config import settings

logger = logging.getLogger(__name__)

# Lazy load sentence-transformers to avoid import errors if not installed
_model = None


def _get_model():
    """Lazy load the embedding model."""
    global _model
    if _model is None:
        try:
            from sentence_transformers import SentenceTransformer
            logger.info(f"Loading embedding model: {settings.EMBEDDING_MODEL}")
            _model = SentenceTransformer(settings.EMBEDDING_MODEL)
            logger.info(f"Embedding model loaded successfully")
        except ImportError:
            logger.error("sentence-transformers not installed. Run: pip install sentence-transformers")
            raise
        except Exception as e:
            logger.error(f"Failed to load embedding model: {str(e)}")
            raise
    return _model


class EmbeddingService:
    """
    Service for generating vector embeddings.
    
    Uses sentence-transformers for local embedding generation.
    Embeddings are used for semantic search functionality.
    """
    
    def __init__(self):
        self.enabled = settings.ENABLE_EMBEDDINGS
        self.batch_size = settings.EMBEDDING_BATCH_SIZE
        self.dimension = settings.EMBEDDING_DIMENSION
        self._model = None
    
    @property
    def model(self):
        """Get the embedding model (lazy loaded)."""
        if not self.enabled:
            return None
        if self._model is None:
            self._model = _get_model()
        return self._model
    
    async def generate_embedding(self, text: str) -> Optional[List[float]]:
        """
        Generate embedding for a single text.
        
        Args:
            text: Text to generate embedding for
            
        Returns:
            List of floats representing the embedding vector,
            or None if embeddings are disabled
        """
        if not self.enabled:
            return None
        
        try:
            # Run in thread pool to avoid blocking
            loop = asyncio.get_event_loop()
            embedding = await loop.run_in_executor(
                None,
                lambda: self.model.encode(text, convert_to_numpy=True).tolist()
            )
            return embedding
        except Exception as e:
            logger.error(f"Failed to generate embedding: {str(e)}")
            return None
    
    async def generate_embeddings_batch(
        self, 
        texts: List[str]
    ) -> List[Optional[List[float]]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to generate embeddings for
            
        Returns:
            List of embedding vectors (or None for failed/disabled)
        """
        if not self.enabled:
            return [None] * len(texts)
        
        if not texts:
            return []
        
        try:
            embeddings = []
            
            # Process in batches
            for i in range(0, len(texts), self.batch_size):
                batch = texts[i:i + self.batch_size]
                logger.debug(f"Generating embeddings for batch {i//self.batch_size + 1}")
                
                # Run in thread pool to avoid blocking
                loop = asyncio.get_event_loop()
                batch_embeddings = await loop.run_in_executor(
                    None,
                    lambda b=batch: self.model.encode(b, convert_to_numpy=True).tolist()
                )
                
                embeddings.extend(batch_embeddings)
            
            logger.info(f"Generated {len(embeddings)} embeddings")
            return embeddings
            
        except Exception as e:
            logger.error(f"Failed to generate batch embeddings: {str(e)}")
            return [None] * len(texts)
    
    def embedding_to_json(self, embedding: Optional[List[float]]) -> Optional[str]:
        """Convert embedding to JSON string for storage."""
        if embedding is None:
            return None
        return json.dumps(embedding)
    
    def json_to_embedding(self, json_str: Optional[str]) -> Optional[List[float]]:
        """Convert JSON string back to embedding list."""
        if json_str is None:
            return None
        try:
            return json.loads(json_str)
        except json.JSONDecodeError:
            return None
    
    def cosine_similarity(
        self, 
        vec1: List[float], 
        vec2: List[float]
    ) -> float:
        """
        Calculate cosine similarity between two vectors.
        
        Args:
            vec1: First embedding vector
            vec2: Second embedding vector
            
        Returns:
            Cosine similarity score (0 to 1)
        """
        try:
            import numpy as np
            v1 = np.array(vec1)
            v2 = np.array(vec2)
            
            dot_product = np.dot(v1, v2)
            norm1 = np.linalg.norm(v1)
            norm2 = np.linalg.norm(v2)
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return float(dot_product / (norm1 * norm2))
        except ImportError:
            # Fallback: pure Python implementation
            dot_product = sum(a * b for a, b in zip(vec1, vec2))
            norm1 = sum(a * a for a in vec1) ** 0.5
            norm2 = sum(b * b for b in vec2) ** 0.5
            
            if norm1 == 0 or norm2 == 0:
                return 0.0
            
            return dot_product / (norm1 * norm2)
        except Exception as e:
            logger.error(f"Failed to calculate cosine similarity: {str(e)}")
            return 0.0


# Global instance
embedding_service = EmbeddingService()
