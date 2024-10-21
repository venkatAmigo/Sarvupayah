import os
import base64
import requests
from PyPDF2 import PdfReader  # Make sure to install PyPDF2 for PDF reading


def extract_text_from_pdf(file_path):
    """Extract text from a PDF file."""
    with open(file_path, "rb") as file:
        reader = PdfReader(file)
        text = ""
        for page in reader.pages:
            text += page.extract_text() + "\n"  # Extract text from each page
    return text.strip()


def index_documents(folder_path):
    for filename in os.listdir(folder_path):
        if filename.endswith(".pdf"):
            file_path = os.path.join(folder_path, filename)
            text_content = extract_text_from_pdf(file_path)  # Extract text from PDF
            base64_data = base64.b64encode(open(file_path, "rb").read()).decode("utf-8")

            document = {
                "data": text_content,  # Store extracted text for searching
                "content_type": "application/pdf",  # Set appropriate MIME type
                "date": "2023-10-05",  # Use an appropriate date format
                "file_name": filename,
                "title": filename  # or a meaningful title for the document
            }

            response = requests.post(
                "http://192.168.1.31:9200/policy_documents/_doc?pipeline=attachment",
                auth=('elastic', 'dJu7Ub1jYsvj622vMHiA'),
                headers={'Content-Type': 'application/json'},
                json=document,
                verify=False
            )

            if response.status_code != 200:
                print(f"Error: {response.status_code} - {response.text}")
            else:
                print(f"Indexed {filename}: {response.status_code}")


if __name__ == "__main__":
    index_documents("../files")
