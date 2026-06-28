"""Resume parsing — extract text from PDF, DOCX, and TXT files."""

from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(uploaded_file):
    """Extract text content from an uploaded PDF file using pypdf."""
    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_text_from_docx(uploaded_file):
    """Extract text content from an uploaded DOCX file using python-docx."""
    doc = Document(uploaded_file)

    text = ""

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_text_from_txt(uploaded_file):
    """Decode an uploaded TXT file as UTF-8 text."""
    return uploaded_file.read().decode("utf-8")


def extract_resume_text(uploaded_file):
    """Route uploaded file to the correct extractor based on extension. Returns text or None."""
    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)

    elif file_name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)

    elif file_name.endswith(".txt"):
        return extract_text_from_txt(uploaded_file)

    return None