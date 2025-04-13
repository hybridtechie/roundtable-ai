import io
import logging
from pathlib import Path
from fastapi import UploadFile, HTTPException

# Configure logger
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

# Try importing optional dependencies
try:
    import pypdf
except ImportError:
    pypdf = None
    logger.warning("pypdf not installed. PDF processing will not be available.")

try:
    from docx import Document
except ImportError:
    Document = None
    logger.warning("python-docx not installed. DOCX processing will not be available.")

SUPPORTED_TEXT_EXTENSIONS = {".txt", ".md", ".json", ".yaml", ".yml", ".csv", ".log"}
SUPPORTED_PDF_EXTENSIONS = {".pdf"}
SUPPORTED_DOCX_EXTENSIONS = {".docx"}

async def read_file_content(file: UploadFile) -> str:

    filename = file.filename or "unknown_file"
    file_extension = Path(filename).suffix.lower()
    logger.info(f"Attempting to read content from file: {filename} (extension: {file_extension})")

    try:
        # Read the file content once into memory
        content_bytes = await file.read()
        logger.debug(f"Read {len(content_bytes)} bytes from file: {filename}")
        if not content_bytes:
            logger.error(f"File '{filename}' is empty or stream was exhausted.")
            raise HTTPException(status_code=400, detail=f"File '{filename}' is empty or could not be read.")

        if file_extension in SUPPORTED_TEXT_EXTENSIONS:
            logger.debug(f"Reading '{filename}' as a text file.")
            try:
                return content_bytes.decode('utf-8')
            except UnicodeDecodeError:
                logger.error(f"Failed to decode file '{filename}' as UTF-8.")
                raise HTTPException(status_code=400, detail=f"Failed to decode file '{filename}' content as UTF-8.")

        elif file_extension in SUPPORTED_PDF_EXTENSIONS:
            if pypdf is None:
                logger.error("pypdf library is required for PDF processing but not installed.")
                raise HTTPException(status_code=501, detail="PDF processing is not available. Please install 'pypdf'.")
            logger.debug(f"Reading '{filename}' as a PDF file.")
            try:
                # Create a BytesIO object for pypdf
                pdf_file = io.BytesIO(content_bytes)
                pdf_reader = pypdf.PdfReader(pdf_file)
                text_content = ""
                for page in pdf_reader.pages:
                    text_content += page.extract_text() or ""  # Add null check
                if not text_content.strip():
                    logger.warning(f"Extracted empty text from PDF: {filename}")
                return text_content
            except Exception as e:
                logger.error(f"Failed to read PDF file '{filename}': {e}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Failed to process PDF file '{filename}'. It might be corrupted or password-protected.")

        elif file_extension in SUPPORTED_DOCX_EXTENSIONS:
            if Document is None:
                logger.error("python-docx library is required for DOCX processing but not installed.")
                raise HTTPException(status_code=501, detail="DOCX processing is not available. Please install 'python-docx'.")
            logger.debug(f"Reading '{filename}' as a DOCX file.")
            try:
                document = Document(io.BytesIO(content_bytes))
                text_content = "\n".join([para.text for para in document.paragraphs])
                if not text_content.strip():
                    logger.warning(f"Extracted empty text from DOCX: {filename}")
                return text_content
            except Exception as e:
                logger.error(f"Failed to read DOCX file '{filename}': {e}", exc_info=True)
                raise HTTPException(status_code=400, detail=f"Failed to process DOCX file '{filename}'. It might be corrupted.")

        else:
            logger.error(f"Unsupported file type: {file_extension} for file '{filename}'")
            supported_types = SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS | SUPPORTED_DOCX_EXTENSIONS
            raise HTTPException(status_code=400, detail=f"Unsupported file type: {file_extension}. Supported types: {', '.join(sorted(supported_types))}")

    except Exception as e:
        # Catch any other unexpected errors during file processing
        logger.error(f"An unexpected error occurred while processing file '{filename}': {e}", exc_info=True)
        # Re-raise HTTPExceptions directly
        if isinstance(e, HTTPException):
            raise e
        # Wrap other exceptions in a generic 500 error
        raise HTTPException(status_code=500, detail=f"An internal error occurred while processing file '{filename}'.")

def get_supported_extensions() -> set:
    """Returns a set of all supported file extensions."""
    return SUPPORTED_TEXT_EXTENSIONS | SUPPORTED_PDF_EXTENSIONS | SUPPORTED_DOCX_EXTENSIONS