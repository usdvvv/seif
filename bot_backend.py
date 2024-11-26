from flask import Flask, request, jsonify
from flask_cors import CORS
import os
import cohere
from werkzeug.utils import secure_filename
from PyPDF2 import PdfReader
import pandas as pd

# Initialize Flask App
app = Flask(__name__)
CORS(app)

# Cohere API Key
COHERE_API_KEY = "PjqW7OWl38pDzRhQt8lzQJmwqdWDxD0IZJznHxeI"  # Replace with your actual Cohere API key
co = cohere.Client(COHERE_API_KEY)  # Initialize Cohere Client

# Directory for Uploaded Files
UPLOAD_FOLDER = "uploads"
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config["UPLOAD_FOLDER"] = UPLOAD_FOLDER

# In-memory Knowledge Base
knowledge_base = ""

# Function to Read Files and Add to Knowledge Base
def process_file(filepath):
    """
    Read the content of a file and add it to the knowledge base.
    Supports text files, PDFs, and CSVs.
    """
    global knowledge_base
    extension = filepath.split(".")[-1].lower()
    content = ""

    try:
        if extension == "txt":  # Process text files
            with open(filepath, "r", encoding="utf-8") as file:
                content = file.read()
        elif extension == "pdf":  # Process PDF files
            reader = PdfReader(filepath)
            for page in reader.pages:
                content += page.extract_text()
        elif extension == "csv":  # Process CSV files
            df = pd.read_csv(filepath)
            content = df.to_string(index=False)
        else:
            return f"Unsupported file type: {extension}"

        # Add the file's content to the knowledge base
        knowledge_base += "\n" + content
        return "File processed successfully."
    except Exception as e:
        return f"Error processing file: {str(e)}"

# Route to Answer Questions
@app.route("/ask", methods=["POST"])
def ask_bot():
    """
    Handle POST requests to answer a question.
    """
    global knowledge_base
    data = request.json
    question = data.get("question", "")

    if not question:
        return jsonify({"error": "No question provided."}), 400

    try:
        # Combine the knowledge base with the user's question
        prompt = f"{knowledge_base}\nQ: {question}\nA:"

        # Send request to Cohere API for question answering
        response = co.generate(
            model="command-light",  # Use a model available in your account
            prompt=prompt,
            max_tokens=300,
            temperature=0.7,
        )

        # Extract the answer from the response
        if response.generations and response.generations[0].text.strip():
            answer = response.generations[0].text.strip()
        else:
            answer = "No valid response generated."

        return jsonify({"answer": answer})
    except Exception as e:
        return jsonify({"error": f"Error: {str(e)}"}), 500

# Route to Upload Files
@app.route("/upload", methods=["POST"])
def upload_file():
    """
    Handle file uploads to expand the knowledge base.
    """
    if "file" not in request.files:
        return jsonify({"error": "No file uploaded."}), 400

    file = request.files["file"]
    if file.filename == "":
        return jsonify({"error": "No file selected."}), 400

    # Save the uploaded file
    filename = secure_filename(file.filename)
    filepath = os.path.join(app.config["UPLOAD_FOLDER"], filename)
    file.save(filepath)

    # Process the uploaded file
    result = process_file(filepath)
    return jsonify({"message": result})

if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000)

