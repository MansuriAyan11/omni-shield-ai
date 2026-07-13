import cloudinary
import cloudinary.uploader
import cloudinary.api
from app.core.config import settings

def configure_cloudinary():
    """Configure Cloudinary with settings"""
    cloudinary.config(
        cloud_name=settings.CLOUDINARY_CLOUD_NAME,
        api_key=settings.CLOUDINARY_API_KEY,
        api_secret=settings.CLOUDINARY_API_SECRET,
        secure=True
    )

def upload_image_to_cloudinary(file_path: str, folder: str = "moderation") -> dict:
    """
    Upload an image to Cloudinary
    
    Args:
        file_path: Path to the image file
        folder: Cloudinary folder name
        
    Returns:
        Dictionary with upload result including secure_url
    """
    try:
        result = cloudinary.uploader.upload(
            file_path,
            folder=folder,
            resource_type="image",
            overwrite=True,
            invalidate=True
        )
        return result
    except Exception as e:
        print(f"Cloudinary upload error: {str(e)}")
        return {}

def delete_image_from_cloudinary(public_id: str) -> bool:
    """
    Delete an image from Cloudinary
    
    Args:
        public_id: Cloudinary public ID of the image
        
    Returns:
        Boolean indicating success
    """
    try:
        result = cloudinary.uploader.destroy(public_id)
        return result.get("result") == "ok"
    except Exception as e:
        print(f"Cloudinary delete error: {str(e)}")
        return False
