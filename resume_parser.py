"""
resume_parser.py

Module for handling input and preprocessing for the AI Resume System.
Supports PDF, DOCX, and TXT files. Extracts, sanitizes, and validates text input.
Implements prompt injection prevention and robust error handling.
"""

import os
from typing import Optional
import logging
from pypdf import PdfReader
from docx import Document
from bs4 import BeautifulSoup

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

SUPPORTED_EXTENSIONS = {'.pdf', '.docx', '.txt'}

class InputValidationError(Exception):
    """Custom exception for input validation errors."""
    pass

def extract_text_from_pdf(file_path: str) -> str:
    """
    Extracts text from a PDF file.
    Args:
        file_path (str): Path to the PDF file.
    Returns:
        str: Extracted text.
    Raises:
        InputValidationError: If the file cannot be read or is empty.
    """
    try:
        reader = PdfReader(file_path)
        text = "\n".join(page.extract_text() or '' for page in reader.pages)
        if not text.strip():
            raise InputValidationError("PDF file contains no extractable text.")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from PDF: {e}")
        raise InputValidationError(f"PDF extraction error: {e}")

def extract_text_from_docx(file_path: str) -> str:
    """
    Extracts text from a DOCX file.
    Args:
        file_path (str): Path to the DOCX file.
    Returns:
        str: Extracted text.
    Raises:
        InputValidationError: If the file cannot be read or is empty.
    """
    try:
        doc = Document(file_path)
        text = "\n".join([para.text for para in doc.paragraphs])
        if not text.strip():
            raise InputValidationError("DOCX file contains no extractable text.")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from DOCX: {e}")
        raise InputValidationError(f"DOCX extraction error: {e}")

def extract_text_from_txt(file_path: str) -> str:
    """
    Extracts text from a TXT file.
    Args:
        file_path (str): Path to the TXT file.
    Returns:
        str: Extracted text.
    Raises:
        InputValidationError: If the file cannot be read or is empty.
    """
    try:
        with open(file_path, 'r', encoding='utf-8') as f:
            text = f.read()
        if not text.strip():
            raise InputValidationError("TXT file is empty.")
        return text
    except Exception as e:
        logger.error(f"Failed to extract text from TXT: {e}")
        raise InputValidationError(f"TXT extraction error: {e}")

def sanitize_text(text: str) -> str:
    """
    Sanitizes text to prevent prompt injection and remove unwanted content.
    - Removes HTML tags
    - Collapses excessive whitespace
    - Removes suspicious prompt tokens (e.g., '###', '>>>', 'User:', 'Assistant:')
    Args:
        text (str): Raw extracted text.
    Returns:
        str: Sanitized text.
    """
    # Remove HTML tags
    soup = BeautifulSoup(text, 'lxml')
    clean_text = soup.get_text()
    # Remove suspicious prompt tokens
    for token in ['###', '>>>', 'User:', 'Assistant:', 'System:', '```']:
        clean_text = clean_text.replace(token, '')
    # Collapse excessive whitespace
    clean_text = ' '.join(clean_text.split())
    return clean_text

def validate_input(file_path: str) -> None:
    """
    Validates the input file for existence, supported extension, and non-empty content.
    Args:
        file_path (str): Path to the input file.
    Raises:
        InputValidationError: If validation fails.
    """
    if not os.path.isfile(file_path):
        raise InputValidationError(f"File does not exist: {file_path}")
    ext = os.path.splitext(file_path)[1].lower()
    if ext not in SUPPORTED_EXTENSIONS:
        raise InputValidationError(f"Unsupported file extension: {ext}")
    if os.path.getsize(file_path) == 0:
        raise InputValidationError("File is empty.")

def parse_input(file_path: str) -> str:
    """
    Main entry point for extracting and sanitizing text from a file.
    Args:
        file_path (str): Path to the input file.
    Returns:
        str: Clean, validated, and sanitized text ready for LLM processing.
    Raises:
        InputValidationError: If extraction or validation fails.
    """
    validate_input(file_path)
    ext = os.path.splitext(file_path)[1].lower()
    if ext == '.pdf':
        raw_text = extract_text_from_pdf(file_path)
    elif ext == '.docx':
        raw_text = extract_text_from_docx(file_path)
    elif ext == '.txt':
        raw_text = extract_text_from_txt(file_path)
    else:
        raise InputValidationError(f"Unsupported file extension: {ext}")
    sanitized = sanitize_text(raw_text)
    if not sanitized:
        raise InputValidationError("Sanitized text is empty.")
    return sanitized 