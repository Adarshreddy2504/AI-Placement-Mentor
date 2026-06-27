from pypdf import PdfReader
from docx import Document


def extract_text_from_pdf(uploaded_file):
    reader = PdfReader(uploaded_file)

    text = ""

    for page in reader.pages:
        page_text = page.extract_text()

        if page_text:
            text += page_text + "\n"

    return text


def extract_text_from_docx(uploaded_file):
    doc = Document(uploaded_file)

    text = ""

    for paragraph in doc.paragraphs:
        text += paragraph.text + "\n"

    return text


def extract_text_from_txt(uploaded_file):
    return uploaded_file.read().decode("utf-8")


def extract_resume_text(uploaded_file):

    file_name = uploaded_file.name.lower()

    if file_name.endswith(".pdf"):
        return extract_text_from_pdf(uploaded_file)

    elif file_name.endswith(".docx"):
        return extract_text_from_docx(uploaded_file)

    elif file_name.endswith(".txt"):
        return extract_text_from_txt(uploaded_file)

    return None