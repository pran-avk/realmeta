"""
Ultra-Lightweight Image Recognition Engine
Uses Perceptual Hashing + Color Histograms for artwork matching
Perfect for free tier hosting - only uses Pillow + numpy (no ML frameworks)
Fast, efficient, and accurate enough for artwork identification
"""
import numpy as np
from PIL import Image
import io
import logging
import imagehash

logger = logging.getLogger('artscope')


def preprocess_image(img, target_size=(256, 256)):
    """
    Preprocess image for feature extraction
    
    Args:
        img: PIL Image, image file path, or bytes
        target_size: Target image size for consistency
    
    Returns:
        PIL Image (preprocessed)
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
        
        # Resize for consistency
        img = img.resize(target_size, Image.Resampling.LANCZOS)
        
        return img
        
    except Exception as e:
        logger.error(f"Image preprocessing failed: {str(e)}")
        raise


def generate_perceptual_hash(image_input):
    """
    Generate perceptual hash for an image
    Robust to minor variations (lighting, angle, compression)
    
    Args:
        image_input: PIL Image, image file path, or bytes
    
    Returns:
        str: Hex string representation of hash
    """
    try:
        img = preprocess_image(image_input)
        
        # Compute multiple hash types for robustness
        phash = imagehash.phash(img, hash_size=16)  # Perceptual hash
        dhash = imagehash.dhash(img, hash_size=16)  # Difference hash
        whash = imagehash.whash(img, hash_size=16)  # Wavelet hash
        
        # Combine hashes into a single string
        combined = f"{phash}|{dhash}|{whash}"
        
        return combined
        
    except Exception as e:
        logger.error(f"Perceptual hash generation failed: {str(e)}")
        raise


def generate_color_histogram(image_input, bins=32):
    """
    Generate color histogram for an image
    Captures color distribution (good for artworks)
    
    Args:
        image_input: PIL Image, image file path, or bytes
        bins: Number of bins per channel
    
    Returns:
        numpy array: Flattened histogram (bins * 3 dimensions)
    """
    try:
        img = preprocess_image(image_input)
        img_array = np.array(img)
        
        # Compute histogram for each RGB channel
        hist_r = np.histogram(img_array[:,:,0], bins=bins, range=(0, 256))[0]
        hist_g = np.histogram(img_array[:,:,1], bins=bins, range=(0, 256))[0]
        hist_b = np.histogram(img_array[:,:,2], bins=bins, range=(0, 256))[0]
        
        # Concatenate and normalize
        hist = np.concatenate([hist_r, hist_g, hist_b])
        hist = hist / hist.sum()  # Normalize to probability distribution
        
        return hist
        
    except Exception as e:
        logger.error(f"Color histogram generation failed: {str(e)}")
        raise


def generate_embedding(image_input):
    """
    Generate combined feature vector (embedding) for an image
    Uses perceptual hash + color histogram
    
    Args:
        image_input: PIL Image, image file path, or bytes
    
    Returns:
        dict: {'hash': str, 'histogram': numpy array}
    """
    try:
        # Generate perceptual hash
        phash = generate_perceptual_hash(image_input)
        
        # Generate color histogram
        histogram = generate_color_histogram(image_input)
        
        # Return combined features
        return {
            'hash': phash,
            'histogram': histogram.tolist()  # Convert to list for JSON serialization
        }
        
    except Exception as e:
        logger.error(f"Embedding generation failed: {str(e)}")
        raise


def compute_hash_similarity(hash1, hash2):
    """
    Compute similarity between two perceptual hashes
    
    Args:
        hash1: Hash string (format: "phash|dhash|whash")
        hash2: Hash string (format: "phash|dhash|whash")
    
    Returns:
        float: Similarity score (0-1, higher is more similar)
    """
    try:
        # Parse hashes
        p1, d1, w1 = hash1.split('|')
        p2, d2, w2 = hash2.split('|')
        
        # Compute Hamming distances (lower is more similar)
        pdist = imagehash.hex_to_hash(p1) - imagehash.hex_to_hash(p2)
        ddist = imagehash.hex_to_hash(d1) - imagehash.hex_to_hash(d2)
        wdist = imagehash.hex_to_hash(w1) - imagehash.hex_to_hash(w2)
        
        # Average distance
        avg_dist = (pdist + ddist + wdist) / 3
        
        # Convert to similarity (0-1, where 1 is identical)
        # Max distance is 256 (16x16 hash), so normalize
        similarity = 1 - (avg_dist / 256)
        
        return max(0.0, min(1.0, similarity))
        
    except Exception as e:
        logger.error(f"Hash similarity computation failed: {str(e)}")
        return 0.0


def compute_histogram_similarity(hist1, hist2):
    """
    Compute similarity between two color histograms
    
    Args:
        hist1: Histogram array
        hist2: Histogram array
    
    Returns:
        float: Similarity score (0-1, higher is more similar)
    """
    try:
        h1 = np.array(hist1)
        h2 = np.array(hist2)
        
        # Normalize if needed
        if h1.sum() > 0:
            h1 = h1 / h1.sum()
        if h2.sum() > 0:
            h2 = h2 / h2.sum()
        
        # Compute correlation (histogram intersection)
        intersection = np.minimum(h1, h2).sum()
        
        return float(intersection)
        
    except Exception as e:
        logger.error(f"Histogram similarity computation failed: {str(e)}")
        return 0.0


def compute_similarity(embedding1, embedding2):
    """
    Compute combined similarity between two embeddings
    Weighted combination of hash and histogram similarity
    
    Args:
        embedding1: First embedding dict
        embedding2: Second embedding dict
    
    Returns:
        float: Similarity score (0-1, higher is more similar)
    """
    try:
        # Extract features
        if isinstance(embedding1, dict):
            hash1 = embedding1.get('hash', '')
            hist1 = embedding1.get('histogram', [])
        else:
            # Legacy format (just histogram)
            hash1 = ''
            hist1 = embedding1
        
        if isinstance(embedding2, dict):
            hash2 = embedding2.get('hash', '')
            hist2 = embedding2.get('histogram', [])
        else:
            # Legacy format (just histogram)
            hash2 = ''
            hist2 = embedding2
        
        # Compute hash similarity (60% weight)
        hash_sim = 0.0
        if hash1 and hash2:
            hash_sim = compute_hash_similarity(hash1, hash2)
        
        # Compute histogram similarity (40% weight)
        hist_sim = 0.0
        if len(hist1) > 0 and len(hist2) > 0:
            hist_sim = compute_histogram_similarity(hist1, hist2)
        
        # Weighted average
        if hash1 and hash2 and len(hist1) > 0 and len(hist2) > 0:
            similarity = 0.6 * hash_sim + 0.4 * hist_sim
        elif hash1 and hash2:
            similarity = hash_sim
        elif len(hist1) > 0 and len(hist2) > 0:
            similarity = hist_sim
        else:
            similarity = 0.0
        
        return float(similarity)
        
    except Exception as e:
        logger.error(f"Similarity computation failed: {str(e)}")
        return 0.0


def find_similar_artworks(query_image, artwork_embeddings, threshold=0.70, top_k=5):
    """
    Find artworks similar to the query image
    
    Args:
        query_image: Image to search for (PIL Image, path, or bytes)
        artwork_embeddings: Dict of {artwork_id: embedding}
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
    """Lightweight image recognition engine (no ML required)"""
    
    def __init__(self):
        logger.info("✅ Lightweight image engine initialized (no ML loading needed)")
    
    def initialize(self):
        """Initialize (instant - no models to load)"""
        pass
    
    def generate_embedding(self, image_input):
        """Generate embedding for an image"""
        return generate_embedding(image_input)
    
    def compute_similarity(self, emb1, emb2):
        """Compute similarity between embeddings"""
        return compute_similarity(emb1, emb2)
    
    def find_similar(self, query_image, artwork_embeddings, threshold=0.70, top_k=5):
        """Find similar artworks"""
        return find_similar_artworks(query_image, artwork_embeddings, threshold, top_k)


# Global instance (instant initialization)
mobilenet_engine = MobileNetEngine()
