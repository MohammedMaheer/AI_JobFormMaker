import os
from PyPDF2 import PdfReader
from docx import Document


def extract_text_from_file(filepath):
    """Extract text content from PDF, DOCX, or TXT files"""
    
    _, ext = os.path.splitext(filepath)
    ext = ext.lower()
    
    try:
        if ext == '.pdf':
            return extract_from_pdf(filepath)
        elif ext == '.docx':
            return extract_from_docx(filepath)
        elif ext == '.txt':
            return extract_from_txt(filepath)
        else:
            raise ValueError(f"Unsupported file format: {ext}")
    except Exception as e:
        print(f"Error extracting text: {str(e)}")
        raise


def extract_from_pdf(filepath):
    """Extract text from PDF file"""
    text = ""
    reader = PdfReader(filepath)
    
    for page in reader.pages:
        page_text = page.extract_text()
        if page_text:
            text += page_text + "\n"
    
    return text.strip()


def extract_from_docx(filepath):
    """Extract text from DOCX file"""
    doc = Document(filepath)
    text = ""
    
    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"
    
    # Also extract text from tables
    for table in doc.tables:
        for row in table.rows:
            for cell in row.cells:
                text += cell.text + " "
            text += "\n"
    
    return text.strip()


def extract_from_txt(filepath):
    """Extract text from TXT file"""
    with open(filepath, 'r', encoding='utf-8') as f:
        return f.read().strip()
