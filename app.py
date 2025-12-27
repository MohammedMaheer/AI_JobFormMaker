import os
import json
import io
from datetime import datetime
import uuid
from flask import Flask, request, jsonify, render_template, send_file, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
from services.file_processor import extract_text_from_file
from services.ai_service import generate_interview_questions, analyze_candidate_with_ai
from services.resume_parser import ResumeParser
from services.candidate_scorer import CandidateScorer
from services.storage_service import StorageService

load_dotenv()

# Initialize services
resume_parser = ResumeParser()
candidate_scorer = CandidateScorer()
storage_service = StorageService()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure upload folder
UPLOAD_FOLDER = 'uploads'
ALLOWED_EXTENSIONS = {'pdf', 'docx', 'txt', 'html', 'htm'}

if not os.path.exists(UPLOAD_FOLDER):
    os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/ranking')
def ranking():
    return render_template('ranking.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/rank', methods=['POST'])
def rank_candidates():
    """Rank candidates based on job description"""
    try:
        job_description = request.form.get('job_description')
        if not job_description:
            return jsonify({'error': 'Job description is required'}), 400
            
        candidates_data = []
        
        if 'resumes' in request.files:
            files = request.files.getlist('resumes')
            for file in files:
                if file and file.filename and allowed_file(file.filename):
                    # Generate unique filename to prevent overwrites
                    ext = file.filename.rsplit('.', 1)[1].lower()
                    unique_filename = f"{uuid.uuid4().hex}_{file.filename}"
                    filepath = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                    file.save(filepath)
                    
                    try:
                        # Parse resume
                        candidate_info = resume_parser.parse_resume(filepath, file.filename)
                        
                        # If parsing failed or returned error
                        if 'error' in candidate_info:
                            print(f"Error parsing {file.filename}: {candidate_info['error']}")
                            # Still add to list so admin can see it failed and view file
                            candidates_data.append({
                                'candidate_name': 'Parsing Failed',
                                'total_score': 0,
                                'breakdown': {'skills_match': 0, 'experience': 0, 'education': 0},
                                'feedback': f"Could not parse resume. Error: {candidate_info['error']}",
                                'file_url': f"/uploads/{unique_filename}",
                                'original_filename': file.filename
                            })
                            continue
                            
                        # Score candidate
                        score_result = candidate_scorer.score_candidate(
                            candidate_info, 
                            job_description, 
                            "Job Position"
                        )
                        
                        # Add file access info
                        score_result['file_url'] = f"/uploads/{unique_filename}"
                        score_result['original_filename'] = file.filename
                        
                        candidates_data.append(score_result)
                    except Exception as e:
                        print(f"Error processing {file.filename}: {str(e)}")
                        # Add error entry
                        candidates_data.append({
                            'candidate_name': 'Error Processing',
                            'total_score': 0,
                            'breakdown': {'skills_match': 0, 'experience': 0, 'education': 0},
                            'feedback': f"Error processing file: {str(e)}",
                            'file_url': f"/uploads/{unique_filename}",
                            'original_filename': file.filename
                        })
                    # Note: We do NOT remove the file here anymore so it can be accessed
        
        # Sort by score
        candidates_data.sort(key=lambda x: x.get('total_score', 0), reverse=True)
        
        return jsonify({
            'success': True,
            'results': candidates_data
        })
        
    except Exception as e:
        print(f"Error ranking candidates: {str(e)}")
        return jsonify({'error': str(e)}), 500


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
            'job_title': job_title,
            'job_description': job_description
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
                    # Email is collected automatically by Google Forms via setCollectEmail(true)
                    {'field': 'Phone Number', 'type': 'phone', 'required': True},
                    {'field': 'Resume/CV Upload', 'type': 'file', 'required': True},
                    {'field': 'LinkedIn Profile', 'type': 'url', 'required': False},
                    {'field': 'Years of Experience', 'type': 'number', 'required': True},
                    {'field': 'Current/Previous Company', 'type': 'text', 'required': False},
                    {'field': 'Expected Salary', 'type': 'text', 'required': False},
                    {'field': 'Availability to Start', 'type': 'date', 'required': True},
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
        
        print(f"\nWebhook Response Status: {response.status_code}")
        print(f"Response Content: {response.text[:500]}")
        
        if response.status_code == 200:
            # Try to parse response for formUrl (from Google Apps Script)
            form_url = None
            try:
                resp_json = response.json()
                print(f"Parsed JSON: {resp_json}")
                if isinstance(resp_json, dict):
                    form_url = resp_json.get('formUrl')
                    print(f"Extracted formUrl: {form_url}")
            except Exception as e:
                print(f"Error parsing response: {e}")
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


@app.route('/api/upload-resume', methods=['POST'])
def upload_resume():
    """Upload and parse candidate resume"""
    try:
        if 'file' not in request.files:
            return jsonify({'error': 'No file provided'}), 400
        
        file = request.files['file']
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Invalid file type. Please upload PDF, DOCX, or TXT'}), 400
        
        # Save file
        filename = file.filename
        file_path = os.path.join(app.config['UPLOAD_FOLDER'], filename)
        file.save(file_path)
        
        # Parse resume
        candidate_info = resume_parser.parse_resume(file_path, filename)
        
        # Clean up file
        try:
            os.remove(file_path)
        except:
            pass
        
        if 'error' in candidate_info:
            return jsonify({'error': candidate_info['error']}), 400
        
        return jsonify({
            'success': True,
            'candidate_info': candidate_info
        })
        
    except Exception as e:
        print(f"Error uploading resume: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/score-candidate', methods=['POST'])
def score_candidate():
    """Score a candidate against job requirements"""
    try:
        data = request.get_json()
        candidate_info = data.get('candidate_info', {})
        job_description = data.get('job_description', '')
        job_title = data.get('job_title', '')
        
        if not candidate_info or not job_description:
            return jsonify({'error': 'Missing required data'}), 400
            
        # Perform AI analysis
        # We use the raw text from the resume if available, otherwise construct a summary
        resume_text = candidate_info.get('raw_text', '')
        if not resume_text:
            resume_text = json.dumps(candidate_info)
            
        ai_analysis = analyze_candidate_with_ai(resume_text, job_description)
        
        # Score the candidate
        score_result = candidate_scorer.score_candidate(
            candidate_info,
            job_description,
            job_title,
            ai_analysis=ai_analysis
        )
        
        # Save to storage
        storage_service.save_candidate(score_result)
        
        return jsonify({
            'success': True,
            'score': score_result
        })
        
    except Exception as e:
        print(f"Error scoring candidate: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/rank-candidates', methods=['POST'])
def rank_candidates_json():
    """Rank multiple candidates"""
    try:
        data = request.get_json()
        scored_candidates = data.get('candidates', [])
        
        if not scored_candidates:
            return jsonify({'error': 'No candidates provided'}), 400
        
        # Rank candidates
        ranked = candidate_scorer.rank_candidates(scored_candidates)
        
        return jsonify({
            'success': True,
            'ranked_candidates': ranked
        })
        
    except Exception as e:
        print(f"Error ranking candidates: {str(e)}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/webhook/application', methods=['POST'])
def webhook_application():
    """
    Webhook to receive job applications from Google Forms/Zapier.
    Expected JSON:
    {
        "name": "John Doe",
        "email": "john@example.com",
        "resume_url": "https://...",
        "job_description": "...",
        "answers": {"Q1": "A1", ...}
    }
    """
    try:
        print("\n" + "!"*50)
        print("WEBHOOK RECEIVED!")
        print("!"*50 + "\n")
        data = request.get_json()
        print(f"Received webhook data: {data.keys()}")
        
        name = data.get('name', 'Unknown Candidate')
        email = data.get('email', '')
        phone = data.get('phone', '')
        resume_url = data.get('resume_url')
        job_description = data.get('job_description', '')
        answers = data.get('answers', {})
        
        # 1. Get Resume Text
        resume_text = ""
        candidate_info = {
            "name": name,
            "email": email,
            "phone": phone,
            "raw_text": ""
        }
        
        if resume_url:
            try:
                # Fix Google Drive URLs for direct download
                if 'drive.google.com' in resume_url:
                    # Extract file ID from various Google Drive URL formats
                    import re
                    file_id_match = re.search(r'/d/([a-zA-Z0-9_-]+)', resume_url) or re.search(r'id=([a-zA-Z0-9_-]+)', resume_url)
                    if file_id_match:
                        file_id = file_id_match.group(1)
                        # Use the correct Google Drive direct download URL
                        resume_url = f"https://drive.google.com/uc?export=download&id={file_id}"
                        print(f"Converted Google Drive URL: {resume_url}")
                
                # Download resume
                response = requests.get(resume_url, allow_redirects=True, timeout=30)
                print(f"Download status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}, Size: {len(response.content)} bytes")
                
                if response.status_code == 200:
                    # Check if we got HTML instead of a file (Google Drive virus scan warning)
                    if response.content[:100].lower().find(b'<!doctype html') != -1 or response.content[:100].lower().find(b'<html') != -1:
                        print("WARNING: Received HTML instead of file. Google Drive may require confirmation.")
                        candidate_info['raw_text'] = f"Resume download blocked by Google Drive. Please use a direct file link or public URL.\nOriginal URL: {resume_url}"
                        resume_text = candidate_info['raw_text']
                    else:
                        # Determine extension from Content-Type or Content-Disposition
                        content_type = response.headers.get('Content-Type', '').lower()
                        content_disposition = response.headers.get('Content-Disposition', '')
                        
                        ext = '.pdf' # Default
                        filename = "resume" # Default filename base
                        
                        if 'application/pdf' in content_type:
                            ext = '.pdf'
                        elif 'wordprocessingml' in content_type or 'msword' in content_type:
                            ext = '.docx'
                        elif 'text/plain' in content_type:
                            ext = '.txt'
                        
                        # Check content disposition for filename
                        if 'filename=' in content_disposition:
                            # Try to extract extension from filename in header
                            fname_match = re.search(r'filename="?([^"]+)"?', content_disposition)
                            if fname_match:
                                fname = fname_match.group(1)
                                filename = fname
                                _, extracted_ext = os.path.splitext(fname)
                                if extracted_ext:
                                    ext = extracted_ext.lower()
                        
                        # Ensure filename has extension
                        if not os.path.splitext(filename)[1]:
                            filename = f"{filename}{ext}"

                        # Save persistently
                        unique_filename = f"{uuid.uuid4().hex}_{filename}"
                        file_path = os.path.join(app.config['UPLOAD_FOLDER'], unique_filename)
                        
                        with open(file_path, 'wb') as f:
                            f.write(response.content)
                        print(f"Saved file: {unique_filename} ({len(response.content)} bytes)")
                    
                        # Parse
                        try:
                            candidate_info = resume_parser.parse_resume(file_path, filename)
                            if 'raw_text' not in candidate_info or not candidate_info['raw_text']:
                                candidate_info['raw_text'] = f"Resume parsing failed. Resume URL: {resume_url}"
                            resume_text = candidate_info.get('raw_text', '')
                            print(f"Successfully parsed resume: {len(resume_text)} characters")
                            
                            # Add file URL for frontend access
                            candidate_info['file_url'] = f"/uploads/{unique_filename}"
                            candidate_info['original_filename'] = filename
                            
                        except Exception as parse_error:
                            print(f"Error parsing resume: {parse_error}")
                            candidate_info['raw_text'] = f"Resume parsing error: {str(parse_error)}\nResume URL: {resume_url}"
                            resume_text = candidate_info['raw_text']
                            # Still provide file access even if parsing failed
                            candidate_info['file_url'] = f"/uploads/{unique_filename}"
                            candidate_info['original_filename'] = filename
                        
                        # Do NOT remove file so it can be viewed later
            except Exception as e:
                print(f"Error downloading/parsing resume: {e}")
                # Fallback if download fails
                candidate_info['raw_text'] = f"Resume URL: {resume_url}"
                resume_text = candidate_info['raw_text']
        
        # If we have answers but no resume text, append answers to text for analysis
        if answers:
            answers_text = "\n".join([f"Q: {k}\nA: {v}" for k, v in answers.items()])
            candidate_info['raw_text'] += f"\n\nInterview Answers:\n{answers_text}"
            resume_text = candidate_info['raw_text']

        # 2. AI Analysis
        ai_analysis = analyze_candidate_with_ai(
            resume_text, 
            job_description, 
            interview_answers=answers
        )
        
        # 3. Score
        print(f"Scoring candidate with {len(candidate_info.get('skills', []))} skills against JD of length {len(job_description)}")
        score_result = candidate_scorer.score_candidate(
            candidate_info,
            job_description,
            "Job Application", # Generic title if not provided
            ai_analysis=ai_analysis
        )
        print(f"Score result: {score_result['total_score']} (Skills: {score_result['breakdown']['skills_match']})")
        
        # 4. Save
        saved_candidate = storage_service.save_candidate(score_result)
        
        return jsonify({
            'success': True,
            'candidate': saved_candidate
        })

    except Exception as e:
        print(f"Webhook Error: {e}")
        return jsonify({'error': str(e)}), 500


@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get all stored candidates"""
    candidates = storage_service.get_all_candidates()
    return jsonify({'candidates': candidates})


@app.route('/api/candidates', methods=['DELETE'])
def clear_candidates():
    """Clear all stored candidates"""
    storage_service.clear_candidates()
    return jsonify({'success': True})


if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port, debug=True)
