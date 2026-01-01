"""OCR for image text extraction."""

import logging
from typing import Optional
from telegram import PhotoSize

logger = logging.getLogger(__name__)


class OCRProcessor:
    """OCR text extraction from images."""
    
    def __init__(self):
        self.enabled = self._check_tesseract()
        if not self.enabled:
            logger.warning("Tesseract OCR not available. Install pytesseract and tesseract OCR engine.")
    
    def _check_tesseract(self) -> bool:
        """Check if Tesseract OCR is available."""
        try:
            import pytesseract
            # Try to get version to verify it's installed
            pytesseract.get_tesseract_version()
            return True
        except Exception as e:
            logger.debug(f"Tesseract not available: {e}")
            return False
    
    async def extract_from_photo(self, photo: PhotoSize, context) -> Optional[str]:
        """
        Extract text from photo using OCR.
        
        Args:
            photo: Telegram photo object
            context: Telegram context for downloading
            
        Returns:
            Extracted text or None
        """
        if not self.enabled:
            logger.debug("OCR not enabled, skipping")
            return None
        
        try:
            # Download photo
            file = await photo.get_file()
            photo_bytes = await file.download_as_bytearray()
            
            return await self._extract_text_from_image(photo_bytes)
            
        except Exception as e:
            logger.error(f"Error processing photo for OCR: {e}")
            return None
    
    async def _extract_text_from_image(self, image_bytes: bytearray) -> Optional[str]:
        """Extract text from image bytes."""
        try:
            from PIL import Image
            import pytesseract
            import io
            
            # Load image
            image_stream = io.BytesIO(image_bytes)
            image = Image.open(image_stream)
            
            # Perform OCR
            text = pytesseract.image_to_string(image)
            
            if text.strip():
                logger.info(f"OCR extracted {len(text)} characters")
                return text.strip()
            else:
                return None
                
        except ImportError as e:
            logger.error(f"OCR library import error: {e}")
            return None
        except Exception as e:
            logger.error(f"OCR processing error: {e}")
            return None