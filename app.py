import requests
import fitz  # PyMuPDF
from flask import Flask, request, jsonify
import os

app = Flask(__name__)

# API Endpoints
LIST_FILES_URL = "https://hamed78.pythonanywhere.com/list_files"
DOWNLOAD_FILE_URL = "https://hamed78.pythonanywhere.com/download_file?file_id={}"
DOWNLOAD_DIR = "downloads"

# Ensure download directory exists
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

def get_pdf_list():
    """Fetches the list of available PDF files from the external API."""
    response = requests.get(LIST_FILES_URL)
    if response.status_code == 200:
        try:
            data = response.json()
            if isinstance(data, list) and all(isinstance(item, str) for item in data):
                print("ERROR: API returned a list of strings instead of dictionaries!")
                return []  # Avoid processing incorrect data
            return data  # Ensure it's a list of dictionaries
        except Exception as e:
            print(f"JSON decoding error: {e}")
            return []
    return []

def download_pdf(file_id, filename):
    """Downloads a PDF file given its ID from the external API."""
    url = DOWNLOAD_FILE_URL.format(file_id)
    print(f"Downloading from: {url}")

    response = requests.get(url, stream=True)
    print(f"Response status: {response.status_code}")

    if response.status_code == 200:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        print(f"File saved at: {filepath}")
        return filepath

    print("Download failed.")
    return None

def download_all_pdfs():
    """Downloads all available PDFs from the external API."""
    pdf_list = get_pdf_list()  # Get all available PDFs
    print(f"Received PDF list: {pdf_list}")  # Debugging print

    if not pdf_list:
        return []

    downloaded_files = []
    
    for pdf in pdf_list:
        if not isinstance(pdf, dict):  # Ensure each item is a dictionary
            print(f"Skipping invalid item: {pdf}")
            continue

        file_id = pdf.get("file_id")
        filename = pdf.get("filename", f"file_{file_id}.pdf")  # Default filename
        filepath = download_pdf(file_id, filename)

        if filepath:
            downloaded_files.append(filepath)

    return downloaded_files

def extract_text_from_pdf(filepath):
    """Extracts text from a PDF file."""
    doc = fitz.open(filepath)
    text = "\n".join([page.get_text("text") for page in doc])
    doc.close()
    return text

def search_text_in_pdfs(query):
    """Searches for a query in all downloaded PDFs and returns matching results."""
    results = []
    for filename in os.listdir(DOWNLOAD_DIR):
        if filename.endswith(".pdf"):
            filepath = os.path.join(DOWNLOAD_DIR, filename)
            text = extract_text_from_pdf(filepath)
            if query.lower() in text.lower():
                results.append({"file": filename, "snippet": text[:500]})  # Show preview
    return results

@app.route("/list_pdfs", methods=["GET"])
def list_pdfs():
    """Returns the list of available PDFs from the external API."""
    return jsonify(get_pdf_list())

@app.route("/download_all", methods=["POST"])
def download_all():
    """Downloads all available PDFs."""
    downloaded_files = download_all_pdfs()
    if downloaded_files:
        return jsonify({"message": "All files downloaded successfully", "files": downloaded_files})
    return jsonify({"error": "Failed to download files"}), 500

@app.route("/search", methods=["POST"])
def search():
    """Searches for a query in downloaded PDFs."""
    data = request.json
    query = data.get("query")
    if not query:
        return jsonify({"error": "Query parameter missing"}), 400
    results = search_text_in_pdfs(query)
    return jsonify(results)

if __name__ == "__main__":
    app.run(debug=True)
