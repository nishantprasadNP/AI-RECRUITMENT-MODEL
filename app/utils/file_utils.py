import os

class ResumeParserError(Exception):
    """Base exception for all errors in the Resume Parser engine."""
    pass

class CorruptedPDFError(ResumeParserError):
    """Exception raised when the PDF file is corrupted or malformed."""
    pass

class EmptyPDFError(ResumeParserError):
    """Exception raised when the PDF has no pages or contains no extractable text."""
    pass

class EncryptedPDFError(ResumeParserError):
    """Exception raised when the PDF is encrypted/password-protected."""
    pass

def validate_pdf_path(pdf_path: str) -> None:
    """
    Validates if the given path points to an existing PDF file.

    Raises:
        FileNotFoundError: If the file does not exist or is a directory.
        ValueError: If the file is not a PDF.
    """
    if not pdf_path:
        raise ValueError("PDF path cannot be empty.")
    
    if not os.path.exists(pdf_path):
        raise FileNotFoundError(f"Resume file not found: {pdf_path}")
        
    if not os.path.isfile(pdf_path):
        raise FileNotFoundError(f"Path is not a valid file: {pdf_path}")
        
    if not pdf_path.lower().endswith(".pdf"):
        raise ValueError(f"File is not a PDF format: {pdf_path}")
