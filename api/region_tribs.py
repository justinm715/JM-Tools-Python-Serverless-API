from flask import Flask, request, jsonify
from PyPDF2 import PdfReader
from datetime import datetime
import random
from tools.foo import RandomNumberGenerator


app = Flask(__name__)


@app.route('/time')
def current_time():
    now = datetime.now().isoformat()
    return jsonify({"time": now})


@app.route('/api/region_tribs/random_number')
def random_number():
    rng = RandomNumberGenerator()
    number = rng.generate()
    return jsonify({"random_number": number})


@app.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            reader = PdfReader(file)
            metadata = reader.metadata
            result = jsonify({
                "author": metadata.author,
                "creator": metadata.creator,
                "producer": metadata.producer,
                "subject": metadata.subject,
                "title": metadata.title,
                "number_of_pages": len(reader.pages)
            })
            print(result)
            return result
        except Exception as e:
            print(e)
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400