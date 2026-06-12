import os
import pytest
import shutil
import fitz  # PyMuPDF

from app.parsers.resume_parser import ResumeParser
from app.utils.file_utils import (
    ResumeParserError,
    CorruptedPDFError,
    EmptyPDFError,
    EncryptedPDFError
)

TEMP_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), "temp_files"))

@pytest.fixture(scope="session", autouse=True)
def setup_test_files():
    """
    Session fixture that dynamically generates test PDF files:
    - Valid PDF containing mock resume text with BAD formatting (to test cleaning).
    - Empty PDF containing a page but no text content.
    - Corrupted PDF with garbage byte content.
    - Encrypted PDF with 256-bit AES protection.
    Cleans up all generated files on test completion.
    """
    os.makedirs(TEMP_DIR, exist_ok=True)
    
    valid_pdf_path = os.path.join(TEMP_DIR, "valid_resume.pdf")
    empty_pdf_path = os.path.join(TEMP_DIR, "empty_resume.pdf")
    corrupted_pdf_path = os.path.join(TEMP_DIR, "corrupted_resume.pdf")
    encrypted_pdf_path = os.path.join(TEMP_DIR, "encrypted_resume.pdf")
    
    # 1. Create Valid PDF with spacing errors to test cleaning heuristics
    doc_valid = fitz.open()
    page_valid = doc_valid.new_page()
    raw_resume_text = (
        "Name\n\n\nJohn Doe\n\n\n\n"
        "Skills\n\nPython\n\nSQL\n\n\n\n"
        "Experience\n\nSoftware Engineer at Tech Corp\n\n\n\n"
        "Education\n\nBachelor of Science in Computer Science"
    )
    page_valid.insert_textbox(fitz.Rect(50, 50, 550, 700), raw_resume_text)
    doc_valid.save(valid_pdf_path)
    doc_valid.close()
    
    # 2. Create Empty PDF
    doc_empty = fitz.open()
    doc_empty.new_page()
    doc_empty.save(empty_pdf_path)
    doc_empty.close()
    
    # 3. Create Corrupted PDF (invalid format bytes)
    with open(corrupted_pdf_path, "wb") as f:
        f.write(b"%PDF-1.4\n%invalid_bytes_completely_ruined\n")
        
    # 4. Create Encrypted PDF
    doc_enc = fitz.open()
    page_enc = doc_enc.new_page()
    page_enc.insert_text(fitz.Point(50, 50), "Classified Resume Data")
    doc_enc.save(
        encrypted_pdf_path,
        encryption=fitz.PDF_ENCRYPT_AES_256,
        owner_pw="owner",
        user_pw="password"
    )
    doc_enc.close()
    
    yield {
        "valid": valid_pdf_path,
        "empty": empty_pdf_path,
        "corrupted": corrupted_pdf_path,
        "encrypted": encrypted_pdf_path,
        "missing": os.path.join(TEMP_DIR, "does_not_exist.pdf"),
        "invalid_ext": os.path.join(TEMP_DIR, "test_resume.txt")
    }
    
    # Clean up files
    shutil.rmtree(TEMP_DIR, ignore_errors=True)

def test_valid_resume_parsing(setup_test_files):
    """Verify that text is extracted successfully from a valid resume PDF."""
    parser = ResumeParser()
    result = parser.extract_text(setup_test_files["valid"])
    
    assert result is not None
    assert "John Doe" in result
    assert "Skills" in result
    assert "Python" in result
    assert "SQL" in result
    assert "Experience" in result
    assert "Software Engineer" in result
    assert "Education" in result

def test_clean_text_heuristics():
    """Verify that text cleaning heuristics correctly clean excessive newlines and spaces."""
    parser = ResumeParser()
    bad_text = (
        "Name\n\n\nJohn Doe\n\n\n\n"
        "Skills\n\nPython\n\nSQL\n\n\n\n"
        "Experience\n\nSoftware Engineer at Tech Corp\n\n\n\n"
        "Education\n\nBachelor of Science in Computer Science"
    )
    
    result = parser._clean_text(bad_text)
    
    expected = (
        "Name\nJohn Doe\n\n"
        "Skills\nPython\nSQL\n\n"
        "Experience\nSoftware Engineer at Tech Corp\n\n"
        "Education\nBachelor of Science in Computer Science"
    )
    assert result == expected

def test_empty_resume_handling(setup_test_files):
    """Verify EmptyPDFError is raised when parsing a PDF with no readable content."""
    parser = ResumeParser()
    with pytest.raises(EmptyPDFError):
        parser.extract_text(setup_test_files["empty"])

def test_corrupted_pdf_handling(setup_test_files):
    """Verify CorruptedPDFError is raised when opening a corrupted PDF file."""
    parser = ResumeParser()
    with pytest.raises(CorruptedPDFError):
        parser.extract_text(setup_test_files["corrupted"])

def test_encrypted_pdf_handling(setup_test_files):
    """Verify EncryptedPDFError is raised when opening a password protected PDF."""
    parser = ResumeParser()
    with pytest.raises(EncryptedPDFError):
        parser.extract_text(setup_test_files["encrypted"])

def test_file_not_found_handling(setup_test_files):
    """Verify FileNotFoundError is raised when a file does not exist."""
    parser = ResumeParser()
    with pytest.raises(FileNotFoundError):
        parser.extract_text(setup_test_files["missing"])

def test_invalid_extension_handling(setup_test_files):
    """Verify ValueError is raised when checking a file with an invalid extension."""
    parser = ResumeParser()
    # Write a dummy txt file
    with open(setup_test_files["invalid_ext"], "w") as f:
        f.write("Raw text file content")
        
    with pytest.raises(ValueError, match="File is not a PDF format"):
        parser.extract_text(setup_test_files["invalid_ext"])
