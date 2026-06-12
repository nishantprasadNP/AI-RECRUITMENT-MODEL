# Resume Parsing Engine (Step 1.1)

A production-ready Python resume parser that extracts and cleans text from PDF resumes. It leverages both `pdfplumber` and `PyMuPDF` (fitz) to ensure optimal text extraction quality, compares the extraction results, and returns the cleanest and longest text output.

## Table of Contents
- [Features](#features)
- [Requirements](#requirements)
- [Project Directory Structure](#project-directory-structure)
- [Setup & Installation](#setup--installation)
  - [1. Create Virtual Environment](#1-create-virtual-environment)
  - [2. Activate Virtual Environment](#2-activate-virtual-environment)
  - [3. Install Dependencies](#3-install-dependencies)
- [How to Run the Parser](#how-to-run-the-parser)
- [How to Run the Tests](#how-to-run-the-tests)
- [Expected Output](#expected-output)
- [Error Handling & Custom Exceptions](#error-handling--custom-exceptions)

---

## Features
- **Dual-Engine Extraction**: Employs both `pdfplumber` and `PyMuPDF` (fitz).
- **Layout-Preserving Text Cleaning**: Normalizes whitespace and line breaks while preserving structural alignment (like keeping headers and list items adjacent and separated from other sections).
- **Quality-Based Text Selection**: Analyzes character distributions to bypass PDF parsing corruption.
- **Robust Exception Mapping**: Captures missing files, empty PDFs, corrupted files, and encrypted PDFs, returning meaningful exceptions.

---

## Requirements
- Python 3.8+
- Packages (defined in `requirements.txt`):
  - `pdfplumber==0.11.1`
  - `pymupdf==1.24.5`
  - `pytest==8.2.2`

---

## Project Directory Structure
```text
project/
│
├── app/
│   ├── parsers/
│   │   └── resume_parser.py
│   │
│   ├── utils/
│   │   └── file_utils.py
│   │
│   └── main.py
│
├── sample_resumes/
│   └── resume.pdf
│
├── tests/
│   └── test_resume_parser.py
│
├── requirements.txt
│
└── README.md
```

---

## Setup & Installation

Follow these steps to set up the environment and run the parser:

### 1. Create Virtual Environment
Create a clean Python virtual environment named `.venv`:
```powershell
python -m venv .venv
```

### 2. Activate Virtual Environment
Activate the environment:
- On **Windows (PowerShell)**:
  ```powershell
  .venv\Scripts\Activate.ps1
  ```
- On **Windows (Command Prompt)**:
  ```cmd
  .venv\Scripts\activate.bat
  ```
- On **macOS/Linux**:
  ```bash
  source .venv/bin/activate
  ```

### 3. Install Dependencies
Install the required packages:
```bash
pip install -r requirements.txt
```

---

## How to Run the Parser

A demonstration program `app/main.py` is included. It is configured to run on the default sample resume or any other PDF path you supply as an argument.

To run the demonstration on the sample resume:
```bash
python app/main.py
```

To parse a custom resume:
```bash
python app/main.py path/to/your_resume.pdf
```

---

## How to Run the Tests

We use `pytest` for unit testing. The test suite dynamically generates test PDF cases (valid, empty, corrupted, encrypted) and runs extraction assertions.

To run the test suite:
```bash
pytest -v tests/
```

---

## Expected Output

When parsing a resume, the parser automatically collapses duplicate blank lines, aligns headings with their text block, and removes spurious list indentation gaps while maintaining a single empty line between sections.

### Example Conversion

**Raw Extracted Content (With layout issues)**:
```text
Name


John Doe



Skills

Python

SQL
```

**Cleaned Output (Preserving layout structure)**:
```text
Name
John Doe

Skills
Python
SQL
```

---

## Error Handling & Custom Exceptions

The module defines the following exceptions in `app/utils/file_utils.py`:
- `FileNotFoundError`: Raised if the resume file does not exist.
- `ValueError`: Raised if the file is not a PDF format.
- `CorruptedPDFError`: Raised if the PDF is malformed or corrupted.
- `EmptyPDFError`: Raised if the PDF has no pages or contains no readable text.
- `EncryptedPDFError`: Raised if the PDF is encrypted/password-protected.
