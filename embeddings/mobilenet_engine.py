"""
MobileNetV2 Image Recognition Engine
Lightweight alternative to CLIP - optimized for free tier hosting
Uses transfer learning with MobileNetV2 for artwork image matching
"""
import numpy as np
from PIL import Image
import io
import logging

logger = logging.getLogger('artscope')

# Lazy loading to save memory
_model = None
_preprocess = None

def load_model():
    """Load MobileNetV2 model (lazy loading)"""
    global _model, _preprocess
    
    if _model is None:
        try:
            from tensorflow.keras.applications import MobileNetV2
            from tensorflow.keras.applications.mobilenet_v2 import preprocess_input
            from tensorflow.keras.preprocessing import image as keras_image
            
            logger.info("Loading MobileNetV2 model...")
            
            # Load pre-trained MobileNetV2 without top layer (for feature extraction)
            _model = MobileNetV2(
                weights='imagenet',
                include_top=False,
                pooling='avg',  # Global average pooling
                input_shape=(224, 224, 3)
            )
            
            _preprocess = preprocess_input
            
            logger.info("✅ MobileNetV2 model loaded successfully")
            
        except Exception as e:
            logger.error(f"Failed to load MobileNetV2: {str(e)}")
            raise
    
    return _model, _preprocess


def preprocess_image(img, target_size=(224, 224)):
    """
    Preprocess image for MobileNetV2
    
    Args:
        img: PIL Image or image file path
        target_size: Target image size (224x224 for MobileNetV2)
    
    Returns:
        Preprocessed numpy array
    """
    try:
        # Load image if path is provided
        if isinstance(img, str):
            img = Image.open(img)
        elif isinstance(img, bytes):
            img = Image.open(io.BytesIO(img))
        
        # Convert to RGB if needed
        if img.mode != 'RGB':
            img = img.convert('RGB')
        
        # Resize image
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        # Convert to numpy array
        img_array = np.array(img)
        
        # Expand dimensions to match model input (1, 224, 224, 3)
        img_array = np.expand_dims(img_array, axis=0)
        
        # Preprocess for MobileNetV2
        _, preprocess_fn = load_model()
        img_array = preprocess_fn(img_array)
        
        return img_array
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        raise


def generate_embedding(image_input):
    """
    Generate embedding vector for an image using MobileNetV2
    
    Args:
        image_input: PIL Image, image file path, or bytes
    
    Returns:
        numpy array: 1280-dimensional feature vector
    """
    try:
        # Load model
        model, _ = load_model()
        
        # Preprocess image
        img_array = preprocess_image(image_input)
        
        # Generate embedding
        embedding = model.predict(img_array, verbose=0)
        
        # Flatten to 1D array
        embedding = embedding.flatten()
        
        # Normalize (L2 normalization)
        norm = np.linalg.norm(embedding)
        if norm > 0:
            embedding = embedding / norm
        
        return embedding
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise


def compute_similarity(embedding1, embedding2):
    """
    Compute cosine similarity between two embeddings
    
    Args:
        embedding1: First embedding vector
        embedding2: Second embedding vector
    
    Returns:
        float: Similarity score (0-1, higher is more similar)
    """
    try:
        # Convert to numpy arrays if needed
        emb1 = np.array(embedding1)
        emb2 = np.array(embedding2)
        
        # Normalize if not already normalized
        norm1 = np.linalg.norm(emb1)
        norm2 = np.linalg.norm(emb2)
        
        if norm1 > 0:
            emb1 = emb1 / norm1
        if norm2 > 0:
            emb2 = emb2 / norm2
        
        # Compute cosine similarity
        similarity = np.dot(emb1, emb2)
        
        # Ensure result is between 0 and 1
        similarity = (similarity + 1) / 2  # Convert from [-1, 1] to [0, 1]
        
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Similarity computation failed: {str(e)}")
        return 0.0


def find_similar_artworks(query_image, artwork_embeddings, threshold=0.7, top_k=5):
    """
    Find artworks similar to the query image
    
    Args:
        query_image: Image to search for (PIL Image, path, or bytes)
        artwork_embeddings: Dict of {artwork_id: embedding_vector}
        threshold: Minimum similarity threshold (0-1)
        top_k: Number of top results to return
    
    Returns:
        list: Sorted list of (artwork_id, similarity_score) tuples
    """
    try:
        # Generate embedding for query image
        query_embedding = generate_embedding(query_image)
        
        # Compare with all artwork embeddings
        similarities = []
        
        for artwork_id, artwork_embedding in artwork_embeddings.items():
            similarity = compute_similarity(query_embedding, artwork_embedding)
            
            if similarity >= threshold:
                similarities.append((artwork_id, similarity))
        
        # Sort by similarity (descending)
        similarities.sort(key=lambda x: x[1], reverse=True)
        
        # Return top k results
        return similarities[:top_k]
        
    except Exception as e:
        logger.error(f"Similar artwork search failed: {str(e)}")
        return []


# Singleton instance
class MobileNetEngine:
    """Singleton wrapper for MobileNetV2 engine"""
    
    def __init__(self):
        self.model = None
        self.preprocess = None
    
    def initialize(self):
        """Initialize the model (call once at startup)"""
        self.model, self.preprocess = load_model()
    
    def generate_embedding(self, image_input):
        """Generate embedding for an image"""
        return generate_embedding(image_input)
    
    def compute_similarity(self, emb1, emb2):
        """Compute similarity between embeddings"""
        return compute_similarity(emb1, emb2)
    
    def find_similar(self, query_image, artwork_embeddings, threshold=0.7, top_k=5):
        """Find similar artworks"""
        return find_similar_artworks(query_image, artwork_embeddings, threshold, top_k)


# Global instance
mobilenet_engine = MobileNetEngine()
