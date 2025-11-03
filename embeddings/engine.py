"""
Optional Advanced Image Embedding Engine using CLIP
(Not required - perceptual hashing is the primary recognition method)
Supports multiple models and caching for performance
"""
try:
    import torch
    import clip
    CLIP_AVAILABLE = True
except ImportError:
    CLIP_AVAILABLE = False
    torch = None
    clip = None

from PIL import Image
import numpy as np
from django.core.cache import cache
from django.conf import settings
import logging

logger = logging.getLogger('artscope')


class EmbeddingEngine:
    """
    Singleton embedding engine with model caching
    """
    
    _instance = None
    _model = None
    _preprocess = None
    _device = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
            cls._instance._initialize()
        return cls._instance
    
    def _initialize(self):
        """Initialize CLIP model (lazy loading) - Optional, falls back to perceptual hashing"""
        if self._model is None:
            if not CLIP_AVAILABLE:
                # CLIP is optional - we use perceptual hashing as the primary method
                logger.info("Using perceptual hashing for image recognition (no ML models needed)")
                return
            
            try:
                self._device = "cuda" if torch.cuda.is_available() else "cpu"
                model_name = settings.ARTSCOPE_CONFIG.get('EMBEDDING_MODEL', 'ViT-B/32')
                
                logger.info(f"Loading CLIP model: {model_name} on {self._device}")
                self._model, self._preprocess = clip.load(model_name, device=self._device)
                self._model.eval()
                
                logger.info("CLIP model loaded successfully")
            except Exception as e:
                logger.error(f"Failed to load CLIP model: {e}")
                # Don't raise, just log - app can run without CLIP
    
    def generate_embedding(self, image_path: str) -> np.ndarray:
        """
        Generate 512-dimensional embedding for an image
        Returns None if CLIP is not available (falls back to perceptual hashing)
        
        Args:
            image_path: Path to the image file
            
        Returns:
            numpy array of shape (512,) or None if CLIP not available
        """
        if not CLIP_AVAILABLE or self._model is None:
            # Perceptual hashing is used instead - no warning needed
            return None
            
        try:
            # Check cache first
            cache_key = f"embedding:{image_path}"
            cached_embedding = cache.get(cache_key)
            if cached_embedding is not None:
                logger.debug(f"Embedding cache hit for {image_path}")
                return cached_embedding
            
            # Load and preprocess image
            image = Image.open(image_path).convert('RGB')
            image_input = self._preprocess(image).unsqueeze(0).to(self._device)
            
            # Generate embedding
            with torch.no_grad():
                embedding = self._model.encode_image(image_input)
                embedding = embedding.cpu().numpy().flatten()
            
            # Normalize embedding
            embedding = embedding / np.linalg.norm(embedding)
            
            # Cache the embedding
            cache_ttl = settings.ARTSCOPE_CONFIG['CACHE_TTL']
            cache.set(cache_key, embedding, cache_ttl)
            
            logger.info(f"Generated embedding for {image_path}")
            return embedding
            
        except Exception as e:
            logger.error(f"Error generating embedding for {image_path}: {e}")
            return None
    
    def batch_generate_embeddings(self, image_paths: list) -> list:
        """
        Generate embeddings for multiple images (batch processing)
        
        Args:
            image_paths: List of image file paths
            
        Returns:
            List of numpy arrays
        """
        embeddings = []
        for path in image_paths:
            embedding = self.generate_embedding(path)
            embeddings.append(embedding)
        return embeddings
    
    def compute_similarity(self, embedding1: np.ndarray, embedding2: np.ndarray) -> float:
        """
        Compute cosine similarity between two embeddings
        
        Args:
            embedding1: First embedding vector
            embedding2: Second embedding vector
            
        Returns:
            Similarity score (0-1)
        """
        similarity = np.dot(embedding1, embedding2) / (
            np.linalg.norm(embedding1) * np.linalg.norm(embedding2)
        )
        return float(similarity)
    
    def find_similar_embeddings(self, query_embedding: np.ndarray, 
                                candidate_embeddings: list, 
                                top_k: int = 5) -> list:
        """
        Find top-k most similar embeddings
        
        Args:
            query_embedding: Query embedding vector
            candidate_embeddings: List of (id, embedding) tuples
            top_k: Number of results to return
            
        Returns:
            List of (id, similarity_score) tuples
        """
        similarities = []
        for artwork_id, embedding in candidate_embeddings:
            similarity = self.compute_similarity(query_embedding, embedding)
            similarities.append((artwork_id, similarity))
        
        # Sort by similarity (descending) and return top-k
        similarities.sort(key=lambda x: x[1], reverse=True)
        return similarities[:top_k]


# Global instance
embedding_engine = EmbeddingEngine()


def generate_text_embedding(text: str) -> np.ndarray:
    """
    Generate embedding for text (for hybrid search)
    
    Args:
        text: Input text
        
    Returns:
        numpy array embedding
    """
    try:
        device = "cuda" if torch.cuda.is_available() else "cpu"
        model_name = settings.ARTSCOPE_CONFIG['EMBEDDING_MODEL']
        model, _ = clip.load(model_name, device=device)
        
        text_tokens = clip.tokenize([text]).to(device)
        with torch.no_grad():
            text_embedding = model.encode_text(text_tokens)
            text_embedding = text_embedding.cpu().numpy().flatten()
        
        # Normalize
        text_embedding = text_embedding / np.linalg.norm(text_embedding)
        return text_embedding
        
    except Exception as e:
        logger.error(f"Error generating text embedding: {e}")
        raise


def hybrid_search(query_embedding: np.ndarray, 
                 query_text: str,
                 artworks: list,
                 alpha: float = 0.7) -> list:
    """
    Hybrid search combining visual and textual similarity
    
    Args:
        query_embedding: Visual embedding
        query_text: Text query
        artworks: List of artwork objects
        alpha: Weight for visual similarity (1-alpha for text)
        
    Returns:
        Ranked list of artworks
    """
    text_embedding = generate_text_embedding(query_text)
    
    scored_artworks = []
    for artwork in artworks:
        # Visual similarity
        visual_sim = embedding_engine.compute_similarity(
            query_embedding, 
            np.array(artwork.embedding)
        )
        
        # Text similarity (based on title, description, tags)
        artwork_text = f"{artwork.title} {artwork.description} {' '.join(artwork.tags)}"
        artwork_text_emb = generate_text_embedding(artwork_text)
        text_sim = embedding_engine.compute_similarity(
            text_embedding,
            artwork_text_emb
        )
        
        # Combined score
        combined_score = alpha * visual_sim + (1 - alpha) * text_sim
        scored_artworks.append((artwork, combined_score))
    
    # Sort by combined score
    scored_artworks.sort(key=lambda x: x[1], reverse=True)
    return scored_artworks
