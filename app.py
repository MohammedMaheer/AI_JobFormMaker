import os
import json
import io
from datetime import datetime
from flask import Flask, request, jsonify, render_template, send_file, Response
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from services.file_processor import extract_text_from_file
from services.ai_service import generate_interview_questions

load_dotenv()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/api/process', methods=['POST'])
def process_job_description():
    """Process job description and generate interview questions"""
    try:
        job_description = ""
        job_title = request.form.get('job_title', 'Job Position')
        num_questions = int(request.form.get('num_questions', 10))
        question_types = request.form.get('question_types', 'mixed')
        ai_provider = request.form.get('ai_provider', 'perplexity')
        api_key = request.form.get('api_key', '')
        
        # Check if file was uploaded
        if 'file' in request.files:
            file = request.files['file']
            if file and file.filename and allowed_file(file.filename):
                # Save file temporarily
                filepath = os.path.join(app.config['UPLOAD_FOLDER'], file.filename)
                file.save(filepath)
                
                # Extract text from file
                job_description = extract_text_from_file(filepath)
                
                # Clean up
                os.remove(filepath)
        
        # Check if text was provided directly
        if not job_description and 'job_description' in request.form:
            job_description = request.form['job_description']
        
        if not job_description:
            return jsonify({'error': 'No job description provided'}), 400
        
        # Generate questions using AI
        questions = generate_interview_questions(
            job_description, 
            job_title,
            num_questions,
            question_types,
            ai_provider,
            api_key
        )
        
        if not questions:
            return jsonify({'error': 'Failed to generate questions'}), 500
        
        return jsonify({
            'success': True,
            'questions': questions,
            'job_title': job_title
        })
        
    except Exception as e:
        print(f"Error processing request: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/send-to-zapier', methods=['POST'])
def send_to_zapier():
    """Send questions to Zapier webhook for Google Sheets/Forms integration"""
    try:
        data = request.get_json()
        questions = data.get('questions', [])
        job_title = data.get('job_title', 'Job Application')
        webhook_url = data.get('webhook_url', '')
        form_type = data.get('form_type', 'sheets')  # 'sheets' or 'application_form'
        company_name = data.get('company_name', '')
        
        if not questions:
            return jsonify({'error': 'No questions provided'}), 400
        
        if not webhook_url:
            return jsonify({'error': 'Zapier webhook URL is required'}), 400
        
        # Prepare data for Zapier based on form type
        if form_type == 'application_form':
            # Format for creating a job application form
            zapier_data = {
                'action': 'create_application_form',
                'form_title': f"Job Application - {job_title}",
                'company_name': company_name,
                'job_title': job_title,
                'timestamp': datetime.now().isoformat(),
                'total_questions': len(questions),
                # Standard application fields
                'standard_fields': [
                    {'field': 'Full Name', 'type': 'text', 'required': True},
                    {'field': 'Email Address', 'type': 'email', 'required': True},
                    {'field': 'Phone Number', 'type': 'phone', 'required': True},
                    {'field': 'Resume/CV Link', 'type': 'url', 'required': False},
                    {'field': 'LinkedIn Profile', 'type': 'url', 'required': False},
                    {'field': 'Years of Experience', 'type': 'number', 'required': True},
                    {'field': 'Current/Previous Company', 'type': 'text', 'required': False},
                    {'field': 'Expected Salary', 'type': 'text', 'required': False},
                    {'field': 'Availability to Start', 'type': 'text', 'required': True},
                ],
                # Interview questions
                'interview_questions': [],
                # Formatted questions as single text for easy use
                'questions_text': '',
                # Individual question fields for Google Forms
                'question_1': '',
                'question_2': '',
                'question_3': '',
                'question_4': '',
                'question_5': '',
                'question_6': '',
                'question_7': '',
                'question_8': '',
                'question_9': '',
                'question_10': '',
            }
            
            questions_text_parts = []
            for i, q in enumerate(questions, 1):
                q_text = q.get('question', '')
                category = q.get('category', 'general')
                
                zapier_data['interview_questions'].append({
                    'number': i,
                    'question': q_text,
                    'category': category,
                    'difficulty': q.get('difficulty', 'medium'),
                    'field_type': 'paragraph'  # Long answer for interview questions
                })
                
                questions_text_parts.append(f"Q{i}. [{category.upper()}] {q_text}")
                
                # Set individual question fields (up to 10)
                if i <= 10:
                    zapier_data[f'question_{i}'] = q_text
            
            zapier_data['questions_text'] = '\n\n'.join(questions_text_parts)
            
        else:
            # Standard sheets format
            zapier_data = {
                'action': 'save_to_sheets',
                'job_title': job_title,
                'timestamp': datetime.now().isoformat(),
                'total_questions': len(questions),
                'questions': [],
                'questions_text': '',
                # Individual fields for easier Zapier mapping
                'question_1': '',
                'question_2': '',
                'question_3': '',
                'question_4': '',
                'question_5': '',
                'question_6': '',
                'question_7': '',
                'question_8': '',
                'question_9': '',
                'question_10': '',
            }
            
            questions_text_parts = []
            for i, q in enumerate(questions, 1):
                q_text = q.get('question', '')
                zapier_data['questions'].append({
                    'number': i,
                    'question': q_text,
                    'category': q.get('category', 'general'),
                    'difficulty': q.get('difficulty', 'medium'),
                    'expected_skills': ', '.join(q.get('expected_skills', []))
                })
                questions_text_parts.append(f"{i}. {q_text}")
                if i <= 10:
                    zapier_data[f'question_{i}'] = q_text
            
            zapier_data['questions_text'] = '\n'.join(questions_text_parts)
        
        # Send to Zapier webhook
        response = requests.post(webhook_url, json=zapier_data, timeout=30)
        
        if response.status_code == 200:
            # Try to parse response for formUrl (from Google Apps Script)
            form_url = None
            try:
                resp_json = response.json()
                if isinstance(resp_json, dict):
                    form_url = resp_json.get('formUrl')
            except:
                pass

            if form_type == 'application_form':
                message = 'Job application form created successfully!'
                if form_url:
                    message += f'<br><br><a href="{form_url}" target="_blank" class="btn btn-primary">View Created Form</a>'
                else:
                    message += ' Check your Google Form.'

                return jsonify({
                    'success': True,
                    'message': message,
                    'formUrl': form_url
                })
            else:
                return jsonify({
                    'success': True,
                    'message': 'Data sent successfully! Check your Google Sheet.'
                })
        else:
            return jsonify({
                'error': f'Zapier returned status {response.status_code}'
            }), 500
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Zapier webhook timed out'}), 500
    except Exception as e:
        print(f"Error sending to Zapier: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/csv', methods=['POST'])
def export_csv():
    """Export questions as CSV file"""
    try:
        data = request.get_json()
        questions = data.get('questions', [])
        job_title = data.get('job_title', 'Interview Questions')
        
        if not questions:
            return jsonify({'error': 'No questions provided'}), 400
        
        # Create CSV content
        csv_content = 'Number,Question,Category,Difficulty,Expected Skills\n'
        for i, q in enumerate(questions, 1):
            question = q.get('question', '').replace('"', '""')
            category = q.get('category', 'general')
            difficulty = q.get('difficulty', 'medium')
            skills = '; '.join(q.get('expected_skills', []))
            csv_content += f'{i},"{question}",{category},{difficulty},"{skills}"\n'
        
        # Return as downloadable file
        return Response(
            csv_content,
            mimetype='text/csv',
            headers={'Content-Disposition': f'attachment; filename=interview-questions-{job_title.replace(" ", "-")}.csv'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/api/export/txt', methods=['POST'])
def export_txt():
    """Export questions as formatted text file"""
    try:
        data = request.get_json()
        questions = data.get('questions', [])
        job_title = data.get('job_title', 'Interview Questions')
        
        if not questions:
            return jsonify({'error': 'No questions provided'}), 400
        
        # Create formatted text content
        txt_content = f"INTERVIEW QUESTIONS\n"
        txt_content += f"Position: {job_title}\n"
        txt_content += f"Generated: {datetime.now().strftime('%Y-%m-%d %H:%M')}\n"
        txt_content += "=" * 60 + "\n\n"
        
        for i, q in enumerate(questions, 1):
            txt_content += f"Question {i}:\n"
            txt_content += f"{q.get('question', '')}\n\n"
            txt_content += f"Category: {q.get('category', 'general')}\n"
            txt_content += f"Difficulty: {q.get('difficulty', 'medium')}\n"
            skills = q.get('expected_skills', [])
            if skills:
                txt_content += f"Expected Skills: {', '.join(skills)}\n"
            txt_content += "-" * 40 + "\n\n"
        
        return Response(
            txt_content,
            mimetype='text/plain',
            headers={'Content-Disposition': f'attachment; filename=interview-questions-{job_title.replace(" ", "-")}.txt'}
        )
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


@app.route('/health')
def health_check():
    return jsonify({'status': 'healthy'})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
