"""File content extraction."""

import io
import logging
from typing import Optional
from telegram import Document

logger = logging.getLogger(__name__)


class FileProcessor:
    """Extract content from various file types."""
    
    def __init__(self):
        self.max_file_size = 10 * 1024 * 1024  # 10MB limit
    
    async def extract_document(self, document: Document, context) -> Optional[str]:
        """
        Extract text content from a document.
        
        Args:
            document: Telegram document object
            context: Telegram context for downloading files
            
        Returns:
            Extracted text content or None
        """
        try:
            # Check file size
            if document.file_size and document.file_size > self.max_file_size:
                logger.warning(f"File too large: {document.file_size} bytes")
                return f"File too large to process: {document.file_name}"
            
            # Get file MIME type
            mime_type = document.mime_type or ""
            
            # Download file
            file = await document.get_file()
            file_bytes = await file.download_as_bytearray()
            
            # Extract based on file type
            if mime_type == "application/pdf" or document.file_name.lower().endswith('.pdf'):
                return await self._extract_pdf(file_bytes)
            
            elif mime_type.startswith("text/") or document.file_name.lower().endswith(('.txt', '.md', '.csv')):
                return await self._extract_text(file_bytes)
            
            elif mime_type in ["application/msword", "application/vnd.openxmlformats-officedocument.wordprocessingml.document"] or \
                 document.file_name.lower().endswith(('.doc', '.docx')):
                return await self._extract_word(file_bytes)
            
            else:
                logger.info(f"Unprocessed file type: {mime_type}")
                return f"[File: {document.file_name} - {mime_type} - {len(file_bytes)} bytes]"
            
        except Exception as e:
            logger.error(f"Error extracting document {document.file_name}: {e}")
            return f"Error processing file {document.file_name}: {str(e)}"
    
    async def _extract_pdf(self, file_bytes: bytearray) -> str:
        """Extract text from PDF."""
        try:
            import PyPDF2
            
            pdf_stream = io.BytesIO(file_bytes)
            pdf_reader = PyPDF2.PdfReader(pdf_stream)
            
            text = []
            for page_num, page in enumerate(pdf_reader.pages[:10]):  # Limit to first 10 pages
                try:
                    page_text = page.extract_text()
                    if page_text:
                        text.append(f"[Page {page_num + 1}]\n{page_text}")
                except Exception as e:
                    logger.warning(f"Could not extract text from page {page_num}: {e}")
            
            full_text = "\n\n".join(text)
            
            # Limit length
            if len(full_text) > 5000:
                full_text = full_text[:5000] + "... [Truncated]"
            
            return full_text if full_text.strip() else "No text extracted from PDF"
            
        except Exception as e:
            logger.error(f"PDF extraction error: {e}")
            return f"PDF file: {len(file_bytes)} bytes (text extraction failed)"
    
    async def _extract_text(self, file_bytes: bytearray) -> str:
        """Extract text from text file."""
        try:
            text = file_bytes.decode('utf-8', errors='ignore')
            
            # Limit length
            if len(text) > 10000:
                text = text[:10000] + "... [Truncated]"
            
            return text
        except Exception as e:
            logger.error(f"Text extraction error: {e}")
            return f"Text file: {len(file_bytes)} bytes (extraction failed)"
    
    async def _extract_word(self, file_bytes: bytearray) -> str:
        """Extract text from Word document."""
        try:
            import docx
            
            word_stream = io.BytesIO(file_bytes)
            doc = docx.Document(word_stream)
            
            text = []
            for para_num, para in enumerate(doc.paragraphs[:100]):  # Limit paragraphs
                if para.text.strip():
                    text.append(para.text)
            
            full_text = "\n\n".join(text)
            
            # Limit length
            if len(full_text) > 5000:
                full_text = full_text[:5000] + "... [Truncated]"
            
            return full_text if full_text.strip() else "No text extracted from Word document"
            
        except ImportError:
            logger.warning("python-docx not installed, cannot extract Word content")
            return f"Word document: {len(file_bytes)} bytes (install python-docx to extract text)"
        except Exception as e:
            logger.error(f"Word extraction error: {e}")
            return f"Word document: {len(file_bytes)} bytes (text extraction failed)"