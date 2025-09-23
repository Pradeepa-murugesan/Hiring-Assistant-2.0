import fitz  
def parse_pdf_from_path(file_path: str) -> str:
    """
    Parses a PDF file from a given path and extracts all its text content.

    This function opens a PDF document using PyMuPDF (fitz), iterates through
    each page, extracts the text, and concatenates it into a single string.

    Args:
        file_path: The absolute or relative path to the PDF file.

    Returns:
        A single string containing all the text from the PDF. Returns an
        error message if the file cannot be opened or read.
    """
    try:
        doc = fitz.open(file_path)
        
        full_text = []
        for page in doc:
            full_text.append(page.get_text())
        
        doc.close()
        
        return "\n".join(full_text)

    except Exception as e:
        print(f"Error reading PDF file at {file_path}: {e}")
        return f"Error: Could not read the PDF file. Details: {e}"