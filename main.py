import os
import sys
import json
import uuid
from flask import Flask, render_template, request, jsonify
from dotenv import load_dotenv

project_root = os.path.dirname(os.path.abspath(__file__))
if project_root not in sys.path:
    sys.path.insert(0, project_root)

from src.utils.pdf_parser import parse_pdf_from_path
from src.core.workflow import app as recruitment_app
from src.agents.job_posting_agent import generate_jd_from_notes
from src.agents.rejection_email_agent import draft_rejection_node 

load_dotenv()
app = Flask(__name__)
UPLOAD_FOLDER = 'uploads'
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/generate_jd', methods=['POST'])
def generate_jd():
    data = request.get_json()
    notes = data.get('notes')
    if not notes:
        return jsonify({"error": "No notes were provided."}), 400
    try:
        generated_jd = generate_jd_from_notes(notes)
        return jsonify({"job_description": generated_jd})
    except Exception as e:
        print(f"Error during JD generation: {e}")
        return jsonify({"error": "An internal server error occurred."}), 500

@app.route('/process', methods=['POST'])
def process():
    """
    This endpoint reliably processes all resumes and returns the results
    in a single, clean batch.
    """
    job_description_text = request.form.get('job_description_text')
    resume_files = request.files.getlist('resumes')

    if not job_description_text or not resume_files:
        return jsonify({"error": "Missing job description or resumes."}), 400

    resume_files.sort(key=lambda x: x.filename)
    
    all_results = []
    for resume_file in resume_files:
        if not resume_file.filename:
            continue

        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], f"{uuid.uuid4()}_{resume_file.filename}")
        resume_file.save(resume_path)
        resume_text = parse_pdf_from_path(resume_path)
        
        initial_state = {
            "job_description": job_description_text,
            "resume_content": resume_text
        }
        final_state = recruitment_app.invoke(initial_state)

        result_for_frontend = {
            "filename": resume_file.filename,
            "state": final_state
        }
        all_results.append(result_for_frontend)
        os.remove(resume_path)

    return jsonify(all_results)

if __name__ == '__main__':
    app.run(port=5001, debug=True)

