import os
from PIL import Image

def save_and_optimize_image(file_storage, upload_folder, filename, max_width=1200, quality=85):
    """
    Saves an uploaded image file, compresses it, generates a thumbnail,
    and returns (saved_filename, thumbnail_filename).
    """
    # Ensure directories exist
    os.makedirs(upload_folder, exist_ok=True)
    
    filepath = os.path.join(upload_folder, filename)
    file_storage.save(filepath)
    
    try:
        with Image.open(filepath) as img:
            # Convert RGBA/P to RGB (necessary for JPEG compression)
            if img.mode in ("RGBA", "P"):
                img = img.convert("RGB")
            
            # Resize large images
            if img.width > max_width:
                height = int((max_width / img.width) * img.height)
                img = img.resize((max_width, height), Image.Resampling.LANCZOS)
            
            # Save original optimized
            img.save(filepath, "JPEG", optimize=True, quality=quality)
            
            # Generate thumbnail
            thumb_name = "thumb_" + filename
            thumb_path = os.path.join(upload_folder, thumb_name)
            img_thumb = img.copy()
            img_thumb.thumbnail((300, 300), Image.Resampling.LANCZOS)
            img_thumb.save(thumb_path, "JPEG", optimize=True, quality=75)
            
            return filename, thumb_name
    except Exception as e:
        # Fallback to direct save
        return filename, filename
