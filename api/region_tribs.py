from flask import Flask, request, jsonify
from pypdf import PdfReader
from datetime import datetime
import random
from tools.foo import RandomNumberGenerator
from tools.region_tribs_tools import AnnotationsExtractor, AreaElementAnalyzer
from werkzeug.utils import secure_filename
import os

app = Flask(__name__)


@app.route('/api/region_tribs/time')
def current_time():
    now = datetime.now().isoformat()
    return jsonify({"time": now})


@app.route('/api/region_tribs/random_number')
def random_number():
    rng = RandomNumberGenerator()
    number = rng.generate()
    return jsonify({"random_number": number})


@app.route('/api/region_tribs/upload-pdf', methods=['POST'])
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


@app.route('/api/region_tribs/process_pdf', methods=['POST'])
def process_pdf():
    if 'file' not in request.files:
        return jsonify({"error": "No file part"}), 400

    file = request.files['file']
    if file.filename == '':
        return jsonify({"error": "No selected file"}), 400

    if file and file.filename.endswith('.pdf'):
        try:
            # Save the file temporarily
            filename = secure_filename(file.filename)
            temp_pdf_path = os.path.join('/tmp', filename)
            file.save(temp_pdf_path)

            # Process the PDF
            extractor = AnnotationsExtractor(temp_pdf_path)
            all_pages_data = []
            for page_num in range(extractor.get_number_of_pages()):
                page_data = extractor.extract_real_world_coordinates(page_num)
                if page_data:
                    analyzer = AreaElementAnalyzer(page_data)
                    area_analysis = analyzer.calculate_intersection_lengths()
                    all_pages_data.append({
                        'page': page_num + 1,
                        'analysis': area_analysis
                    })

            # Clean up: remove the temporary file
            os.remove(temp_pdf_path)

            return jsonify(all_pages_data)

        except Exception as e:
            return jsonify({"error": str(e)}), 500

    return jsonify({"error": "Invalid file type"}), 400
