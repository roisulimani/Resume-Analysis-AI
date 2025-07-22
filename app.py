"""
app.py

Flask web app for the AI Resume System. Provides a modern, minimal UI for uploading a job description and resume, running the analysis, and displaying results.
Follows all UI Design Requirements from .cursorrules.
"""

import os
from flask import Flask, render_template, request, redirect, url_for, flash
from werkzeug.utils import secure_filename
from resume_parser import parse_input, InputValidationError
from llm_orchestrator import analyze_resume, AnalysisResult
from output_formatter import format_human_readable_summary, format_result_as_json
import json

UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

app = Flask(__name__)
app.secret_key = 'stampli_secret_key'  # For flash messages
app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER

os.makedirs(UPLOAD_FOLDER, exist_ok=True)

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS

@app.route('/', methods=['GET', 'POST'])
def index():
    if request.method == 'POST':
        job_file = request.files.get('job')
        resume_file = request.files.get('resume')
        if not job_file or not allowed_file(job_file.filename):
            flash('Please upload a valid job description file (PDF, DOCX, or TXT).')
            return redirect(request.url)
        if not resume_file or not allowed_file(resume_file.filename):
            flash('Please upload a valid resume file (PDF, DOCX, or TXT).')
            return redirect(request.url)
        job_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(job_file.filename))
        resume_path = os.path.join(app.config['UPLOAD_FOLDER'], secure_filename(resume_file.filename))
        job_file.save(job_path)
        resume_file.save(resume_path)
        try:
            job_desc = parse_input(job_path)
            resume = parse_input(resume_path)
        except InputValidationError as e:
            flash(f'Input error: {e}')
            return redirect(request.url)
        except Exception as e:
            flash(f'Unexpected error: {e}')
            return redirect(request.url)
        try:
            result: AnalysisResult = analyze_resume(job_desc, resume)
            summary = format_human_readable_summary(result)
            json_output = format_result_as_json(result)
            parsed_result = json.loads(json_output)
            return render_template('index.html', summary=summary, json_output=json_output, parsed_result=parsed_result, logo_url=url_for('static', filename='stampli.png'))
        except Exception as e:
            flash(f'LLM analysis error: {e}')
            return redirect(request.url)
    return render_template('index.html', summary=None, json_output=None, parsed_result=None, logo_url=url_for('static', filename='stampli.png'))

if __name__ == '__main__':
    app.run(debug=True) 