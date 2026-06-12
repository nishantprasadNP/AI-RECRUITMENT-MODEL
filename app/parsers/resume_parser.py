import logging
import re
import pdfplumber
import fitz  # PyMuPDF
from pdfminer.pdfdocument import PDFPasswordIncorrect
from pdfminer.pdfparser import PDFSyntaxError

from app.utils.file_utils import (
    validate_pdf_path,
    ResumeParserError,
    CorruptedPDFError,
    EmptyPDFError,
    EncryptedPDFError
)

# Setup module-level logger
logger = logging.getLogger("resume_parser")

class ResumeParser:
    """
    A production-ready resume parser that extracts and cleans text from PDF resumes
    using both pdfplumber and PyMuPDF (fitz) engines, returning the highest-quality result.
    """

    def extract_with_pdfplumber(self, pdf_path: str) -> str:
        """
        Extracts raw text from a PDF file using pdfplumber.

        Args:
            pdf_path: Absolute or relative path to the PDF file.

        Returns:
            The raw extracted text string.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a PDF.
            EncryptedPDFError: If the PDF is password-protected.
            EmptyPDFError: If the PDF contains no pages or extractable text.
            CorruptedPDFError: If the PDF structure is corrupted.
        """
        validate_pdf_path(pdf_path)
        
        try:
            with pdfplumber.open(pdf_path) as pdf:
                if not pdf.pages:
                    raise EmptyPDFError(f"PDF contains no pages: {pdf_path}")
                
                text_parts = []
                for page in pdf.pages:
                    page_text = page.extract_text()
                    if page_text:
                        text_parts.append(page_text)
                
                raw_text = "\n".join(text_parts)
                if not raw_text.strip():
                    raise EmptyPDFError(f"PDF has pages but contains no extractable text: {pdf_path}")
                
                return raw_text
        except PDFPasswordIncorrect as e:
            raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}") from e
        except PDFSyntaxError as e:
            raise CorruptedPDFError(f"Corrupted PDF syntax: {pdf_path}") from e
        except EmptyPDFError:
            raise
        except Exception as e:
            err_msg = str(e).lower()
            if "password" in err_msg or "encrypt" in err_msg:
                raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}") from e
            raise CorruptedPDFError(f"Failed to parse PDF with pdfplumber: {str(e)}") from e

    def extract_with_pymupdf(self, pdf_path: str) -> str:
        """
        Extracts raw text from a PDF file using PyMuPDF.

        Args:
            pdf_path: Absolute or relative path to the PDF file.

        Returns:
            The raw extracted text string.

        Raises:
            FileNotFoundError: If the file does not exist.
            ValueError: If the file is not a PDF.
            EncryptedPDFError: If the PDF is password-protected.
            EmptyPDFError: If the PDF contains no pages or extractable text.
            CorruptedPDFError: If the PDF structure is corrupted.
        """
        validate_pdf_path(pdf_path)
        
        try:
            with fitz.open(pdf_path) as doc:
                if doc.is_encrypted:
                    raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}")
                
                if doc.page_count == 0:
                    raise EmptyPDFError(f"PDF contains no pages: {pdf_path}")
                
                text_parts = []
                for page in doc:
                    page_text = page.get_text()
                    if page_text:
                        text_parts.append(page_text)
                
                raw_text = "\n".join(text_parts)
                if not raw_text.strip():
                    raise EmptyPDFError(f"PDF has pages but contains no extractable text: {pdf_path}")
                
                return raw_text
        except (EmptyPDFError, EncryptedPDFError):
            raise
        except Exception as e:
            err_msg = str(e).lower()
            if "encrypted" in err_msg or "password" in err_msg:
                raise EncryptedPDFError(f"PDF is encrypted: {pdf_path}") from e
            raise CorruptedPDFError(f"Failed to parse PDF with PyMuPDF: {str(e)}") from e

    def extract_text(self, pdf_path: str) -> str:
        """
        Extracts and cleans text from the PDF using both pdfplumber and PyMuPDF,
        comparing the results and returning the longer and cleaner text output.

        Args:
            pdf_path: Absolute or relative path to the PDF file.

        Returns:
            The cleaned extracted resume text.
        """
        logger.info(f"Loaded file: {pdf_path}")
        
        pdfplumber_text = None
        pymupdf_text = None
        pdfplumber_err = None
        pymupdf_err = None

        # 1. Attempt pdfplumber
        try:
            logger.info(f"Method used: pdfplumber for {pdf_path}")
            raw_text_plumber = self.extract_with_pdfplumber(pdf_path)
            pdfplumber_text = self._clean_text(raw_text_plumber)
            logger.info(f"Extraction success: pdfplumber. Character count: {len(pdfplumber_text)}")
        except Exception as e:
            pdfplumber_err = e
            logger.warning(f"Extraction failure: pdfplumber on {pdf_path}. Reason: {str(e)}")

        # 2. Attempt PyMuPDF
        try:
            logger.info(f"Method used: PyMuPDF for {pdf_path}")
            raw_text_pymupdf = self.extract_with_pymupdf(pdf_path)
            pymupdf_text = self._clean_text(raw_text_pymupdf)
            logger.info(f"Extraction success: PyMuPDF. Character count: {len(pymupdf_text)}")
        except Exception as e:
            pymupdf_err = e
            logger.warning(f"Extraction failure: PyMuPDF on {pdf_path}. Reason: {str(e)}")

        # 3. Compare and select output
        if pdfplumber_text is not None and pymupdf_text is not None:
            best_text = self._compare_text(pdfplumber_text, pymupdf_text)
            selected_method = "pdfplumber" if best_text == pdfplumber_text else "PyMuPDF"
            logger.info(f"Comparison: Selected {selected_method} result as it is cleaner and longer. Final character count: {len(best_text)}")
            return best_text
        elif pdfplumber_text is not None:
            logger.info(f"Comparison: Only pdfplumber succeeded. Character count: {len(pdfplumber_text)}")
            return pdfplumber_text
        elif pymupdf_text is not None:
            logger.info(f"Comparison: Only PyMuPDF succeeded. Character count: {len(pymupdf_text)}")
            return pymupdf_text
        else:
            # Both failed. If they failed due to validation issues or specific errors, propagate
            # Check for specific Exceptions
            for err in (pdfplumber_err, pymupdf_err):
                if isinstance(err, (FileNotFoundError, ValueError, EncryptedPDFError, EmptyPDFError, CorruptedPDFError)):
                    raise err
            # Default fallback
            raise ResumeParserError(
                f"Failed to extract text using both extraction methods. "
                f"pdfplumber error: {pdfplumber_err}. PyMuPDF error: {pymupdf_err}"
            )

    def _clean_text(self, text: str) -> str:
        """
        Applies smart cleanups to preserve resume structure:
        - Normalizes all line breaks (converting CRLF/CR to LF).
        - Collapses excessive horizontal spaces to a single space.
        - Collapses duplicate blank lines into a single blank line.
        - Uses line analysis heuristics to delete blank lines that fragment list items or split labels from values.
        """
        if not text:
            return ""

        # Normalize line breaks
        text = text.replace("\r\n", "\n").replace("\r", "\n")

        # Split into lines
        lines = text.split("\n")
        cleaned_lines = []

        # Common resume section titles
        label_headings = {
            "name", "skills", "education", "experience", "work experience",
            "projects", "summary", "languages", "interests", "hobbies",
            "contact", "phone", "email", "address", "links", "certifications",
            "awards", "profile", "about me", "professional summary", "technical skills"
        }

        for line in lines:
            # Remove redundant horizontal spaces
            cleaned_line = re.sub(r"[ \t]+", " ", line).strip()
            cleaned_lines.append(cleaned_line)

        result_lines = []
        for i, line in enumerate(cleaned_lines):
            # Skip initial empty lines
            if not line:
                if not result_lines:
                    continue
                # Skip duplicate consecutive empty lines
                if result_lines[-1] == "":
                    continue

                # Context-aware blank line removal heuristics
                prev_line = result_lines[-1]
                next_line = None
                for j in range(i + 1, len(cleaned_lines)):
                    if cleaned_lines[j]:
                        next_line = cleaned_lines[j]
                        break

                if prev_line:
                    # Case 1: Previous line is a section heading or ends in a colon, e.g. "Skills:" -> remove blank line
                    prev_lower = prev_line.lower().strip(":-•*")
                    if prev_lower in label_headings or prev_line.endswith(":"):
                        continue

                    if next_line:
                        # Skip keeping a blank line if the next line is a header itself
                        # because we actually DO want a blank line before headers to separate sections
                        next_lower = next_line.lower().strip(":-•*")
                        if next_lower in label_headings:
                            result_lines.append("")
                            continue

                        # Case 2: Short consecutive lines (e.g. list items, labels/values) -> remove blank line
                        prev_words = prev_line.split()
                        next_words = next_line.split()
                        if len(prev_words) <= 3 and len(next_words) <= 3:
                            continue

                        # Case 3: Next line starts with a list bullet -> remove blank line
                        if next_line.startswith(("-", "*", "•", "▪", "◦", "▪")) or (next_words and next_words[0].endswith(".") and next_words[0][:-1].isdigit()):
                            continue

                result_lines.append("")
            else:
                result_lines.append(line)

        # Trim trailing empty lines
        while result_lines and result_lines[-1] == "":
            result_lines.pop()

        return "\n".join(result_lines)

    def _compare_text(self, text1: str, text2: str) -> str:
        """
        Compares two texts using a quality metric:
        score = cleaned_length * (alphanumeric_or_space_chars / total_chars)
        This penalizes documents with high ratios of corrupted punctuation or binary gibberish.
        Returns the higher scoring text.
        """
        if not text1:
            return text2
        if not text2:
            return text1

        def get_score(text: str) -> float:
            total_len = len(text)
            if total_len == 0:
                return 0.0
            alnum_spaces = sum(c.isalnum() or c.isspace() for c in text)
            ratio = alnum_spaces / total_len
            return total_len * ratio

        score1 = get_score(text1)
        score2 = get_score(text2)

        return text1 if score1 >= score2 else text2
