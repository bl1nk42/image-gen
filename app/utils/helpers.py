import hashlib
import json
from typing import Dict, Any


def generate_cache_key(prompt: str, style: str = None, aspect_ratio: str = "1:1") -> str:
    """
    Generate a cache key based on the image generation parameters
    
    Args:
        prompt: The text prompt for image generation
        style: The style of the image (optional)
        aspect_ratio: The aspect ratio of the image
        
    Returns:
        A unique cache key string
    """
    # Create a dictionary with all parameters
    params = {
        "prompt": prompt,
        "style": style,
        "aspect_ratio": aspect_ratio
    }
    
    # Convert to JSON string for consistent hashing
    params_str = json.dumps(params, sort_keys=True, ensure_ascii=False)
    
    # Generate SHA256 hash
    hash_obj = hashlib.sha256(params_str.encode('utf-8'))
    hash_hex = hash_obj.hexdigest()
    
    # Return cache key with prefix
    return f"img_cache:{hash_hex}"


def validate_aspect_ratio(aspect_ratio: str) -> bool:
    """
    Validate if the aspect ratio is in correct format
    
    Args:
        aspect_ratio: The aspect ratio string (e.g., "1:1", "16:9")
        
    Returns:
        True if valid, False otherwise
    """
    if not aspect_ratio:
        return False
        
    parts = aspect_ratio.split(":")
    if len(parts) != 2:
        return False
        
    try:
        width = int(parts[0])
        height = int(parts[1])
        return width > 0 and height > 0
    except ValueError:
        return False

