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
        return response.json()
    return []

def download_pdf(file_id, filename):
    """Downloads a PDF file given its ID from the external API."""
    response = requests.get(DOWNLOAD_FILE_URL.format(file_id), stream=True)
    if response.status_code == 200:
        filepath = os.path.join(DOWNLOAD_DIR, filename)
        with open(filepath, "wb") as f:
            for chunk in response.iter_content(1024):
                f.write(chunk)
        return filepath
    return None

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

@app.route("/download", methods=["POST"])
def download():
    """Downloads a specific PDF given a file_id."""
    data = request.json
    file_id = data.get("file_id")
    filename = data.get("filename", "downloaded_file.pdf")
    if not file_id:
        return jsonify({"error": "file_id parameter is required"}), 400
    filepath = download_pdf(file_id, filename)
    if filepath:
        return jsonify({"message": "File downloaded successfully", "filepath": filepath})
    return jsonify({"error": "Failed to download file"}), 500

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
