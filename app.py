import os
import json
import io
import tempfile
from datetime import datetime
import uuid
from flask import Flask, request, jsonify, render_template, send_file, Response, send_from_directory
from flask_cors import CORS
from dotenv import load_dotenv
import requests
import gdown
from services.file_processor import extract_text_from_file
from services.ai_service import generate_interview_questions, analyze_candidate_with_ai, format_job_description
from services.resume_parser import ResumeParser
from services.candidate_scorer import CandidateScorer
from services.storage_service import StorageService
from services.email_service import EmailService

load_dotenv()

# Initialize services
resume_parser = ResumeParser()
candidate_scorer = CandidateScorer()
storage_service = StorageService()
email_service = EmailService()

app = Flask(__name__, static_folder='static', template_folder='templates')
CORS(app)

# Configure upload folder
# Use /tmp for Vercel/Cloud, or local 'uploads' folder for development
if os.environ.get('VERCEL') or os.environ.get('RAILWAY_ENVIRONMENT'):
    UPLOAD_FOLDER = '/tmp'
else:
    UPLOAD_FOLDER = 'uploads'
    if not os.path.exists(UPLOAD_FOLDER):
        os.makedirs(UPLOAD_FOLDER)

app.config['UPLOAD_FOLDER'] = UPLOAD_FOLDER
app.config['MAX_CONTENT_LENGTH'] = 16 * 1024 * 1024  # 16MB max file size

ALLOWED_EXTENSIONS = {'pdf', 'doc', 'docx', 'txt'}

def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


# ============================================================
# HEALTH CHECK & DIAGNOSTICS
# ============================================================
@app.route('/api/health')
def health_check():
    """Health check endpoint for monitoring and deployment verification"""
    is_vercel = bool(os.environ.get('VERCEL'))
    is_postgres = storage_service.is_postgres
    
    return jsonify({
        'status': 'healthy',
        'environment': 'vercel' if is_vercel else 'local',
        'database': 'postgresql' if is_postgres else 'sqlite',
        'timestamp': datetime.now().isoformat()
    })


@app.route('/api/debug/config')
def debug_config():
    """Debug endpoint to check configuration (development only)"""
    if os.environ.get('VERCEL'):
        return jsonify({'error': 'Debug endpoint disabled in production'}), 403
    
    return jsonify({
        'environment': {
            'VERCEL': bool(os.environ.get('VERCEL')),
            'DATABASE_URL': '***' if os.environ.get('DATABASE_URL') else None,
            'GOOGLE_SCRIPT_URL': bool(os.environ.get('GOOGLE_SCRIPT_URL')),
            'NGROK_AUTH_TOKEN': bool(os.environ.get('NGROK_AUTH_TOKEN')),
            'AI_PROVIDER': os.environ.get('AI_PROVIDER', 'perplexity'),
        },
        'storage': {
            'is_postgres': storage_service.is_postgres,
            'jobs_count': len(storage_service.get_all_jobs()),
            'candidates_count': len(storage_service.get_all_candidates()),
        }
    })


# ============================================================
# PAGE ROUTES
# ============================================================
@app.route('/')
def dashboard():
    return render_template('dashboard.html')

@app.route('/create-job')
def create_job_page():
    return render_template('index.html')

@app.route('/jobs/<job_id>')
def job_details(job_id):
    return render_template('job_details.html', job_id=job_id)

@app.route('/ranking')
def ranking():
    return render_template('ranking.html')


@app.route('/uploads/<filename>')
def uploaded_file(filename):
    return send_from_directory(app.config['UPLOAD_FOLDER'], filename)


@app.route('/api/jobs', methods=['GET'])
def get_jobs():
    jobs = storage_service.get_all_jobs()
    return jsonify({'jobs': jobs})

@app.route('/api/jobs/<job_id>', methods=['GET'])
def get_job(job_id):
    job = storage_service.get_job(job_id)
    if not job:
        return jsonify({'error': 'Job not found'}), 404
    return jsonify({'job': job})

@app.route('/api/jobs/<job_id>/candidates', methods=['GET'])
def get_job_candidates(job_id):
    candidates = storage_service.get_all_candidates(job_id=job_id)
    return jsonify({'candidates': candidates})

@app.route('/api/jobs/<job_id>/close', methods=['POST'])
def close_job(job_id):
    """Mark a job as closed (inactive) and stop Google Form responses"""
    print(f"Attempting to close job: {job_id}")
    try:
        # 1. Get job details to find script_url and edit_url
        job = storage_service.get_job(job_id)
        if not job:
            return jsonify({'success': False, 'error': 'Job not found'}), 404

        # 2. Try to close the Google Form if we have the URL
        script_url = job.get('script_url')
        edit_url = job.get('edit_url')
        
        if script_url and edit_url:
            print(f"Closing Google Form via Script: {script_url}")
            try:
                payload = {
                    'action': 'close_form',
                    'form_url': edit_url
                }
                resp = requests.post(script_url, json=payload, timeout=10)
                print(f"Google Script Response: {resp.text}")
            except Exception as e:
                print(f"Warning: Failed to close Google Form remotely: {e}")
                # We continue to close it locally anyway

        # 3. Update local status
        success = storage_service.update_job_status(job_id, 'closed')
        if success:
            print(f"Successfully closed job: {job_id}")
            return jsonify({'success': True})
        else:
            print(f"Failed to close job: {job_id} (DB error)")
            return jsonify({'success': False, 'error': 'Failed to update job status'}), 500
            
    except Exception as e:
        print(f"Exception closing job {job_id}: {e}")
        return jsonify({'success': False, 'error': str(e)}), 500


@app.route('/api/jobs/<job_id>', methods=['DELETE'])
def delete_job(job_id):
    """Delete a job and its candidates"""
    try:
        # 1. Get job details to find script_url and edit_url
        job = storage_service.get_job(job_id)
        if job:
            script_url = job.get('script_url')
            edit_url = job.get('edit_url')
            
            if script_url and edit_url:
                print(f"Deleting Google Form via Script: {script_url}")
                try:
                    payload = {
                        'action': 'delete_form',
                        'form_url': edit_url
                    }
                    requests.post(script_url, json=payload, timeout=10)
                except Exception as e:
                    print(f"Warning: Failed to delete Google Form remotely: {e}")

        success = storage_service.delete_job(job_id)
        if success:
            return jsonify({'success': True})
        else:
            return jsonify({'success': False, 'error': 'Failed to delete job'}), 500
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


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
                # Create Job in Database
                job_data = None
                try:
                    # Format description with AI
                    raw_description = data.get('job_description', '')
                    formatted_description = format_job_description(raw_description)
                    
                    job_data = {
                        'title': job_title,
                        'description': formatted_description,
                        'form_url': form_url,
                        'edit_url': resp_json.get('editUrl') if resp_json else None,
                        'script_url': webhook_url, # Save the script URL to control the form later
                        'status': 'active',
                        'questions': questions,
                        'company_name': company_name
                    }
                    storage_service.create_job(job_data)
                    print(f"Job created: {job_title}")
                except Exception as e:
                    print(f"Error creating job record: {e}")
                    # Fallback if AI fails or other error
                    if not job_data:
                         job_data = {
                            'title': job_title,
                            'description': data.get('job_description', ''),
                            'form_url': form_url,
                            'edit_url': resp_json.get('editUrl') if resp_json else None,
                            'script_url': webhook_url,
                            'status': 'active',
                            'questions': questions,
                            'company_name': company_name
                        }
                         try:
                             storage_service.create_job(job_data)
                         except:
                             pass

                message = 'Job application form created successfully!'
                if form_url:
                    message += f'<br><br><a href="{form_url}" target="_blank" class="btn btn-primary">View Created Form</a>'
                else:
                    message += ' Check your Google Form.'

                return jsonify({
                    'success': True,
                    'message': message,
                    'formUrl': form_url,
                    'jobId': job_data.get('id') if job_data else None
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
    """
    try:
        print("\n" + "!"*50)
        print("WEBHOOK RECEIVED!")
        print("!"*50 + "\n")
        data = request.get_json()
        print(f"Received webhook data: {data.keys()}")
        
        # Try to link to a Job FIRST (needed for duplicate check)
        job_id = None
        job_desc_from_form = data.get('job_description', '') or ''
        
        # Search active jobs to find a match
        try:
            active_jobs = storage_service.get_all_jobs()
            print(f"Job matching: Found {len(active_jobs)} jobs, form description: '{job_desc_from_form[:50]}...'")
            
            # Strategy 1: Match by job title in form description
            for job in active_jobs:
                # Only match ACTIVE jobs
                if job.get('status') != 'active':
                    continue
                    
                # Check if job title is in the form description (e.g. "Job Application for Software Engineer")
                if job.get('title') and job.get('title') in job_desc_from_form:
                    job_id = job['id']
                    print(f"✓ Matched by title: {job_id} ({job['title']})")
                    
                    # Use the FULL JD from the database for better scoring
                    if job.get('description'):
                        print("Using full JD from database for scoring.")
                        data['job_description'] = job['description']
                    break
            
            # Strategy 2: If only one active job and no match found, assign to it
            if not job_id:
                active_only = [j for j in active_jobs if j.get('status') == 'active']
                if len(active_only) == 1:
                    job = active_only[0]
                    job_id = job['id']
                    print(f"✓ Auto-assigned to only active job: {job_id} ({job['title']})")
                    if job.get('description'):
                        data['job_description'] = job['description']
                elif len(active_only) == 0:
                    print("⚠️ No active jobs found!")
                else:
                    print(f"⚠️ Multiple active jobs ({len(active_only)}), couldn't auto-match")
                    
        except Exception as e:
            print(f"Error matching job: {e}")

        if job_id:
            data['job_id'] = job_id
        else:
            print("⚠️ WARNING: No job_id assigned to this application!")
        
        # Check for duplicates (debounce) - now includes job_id
        email = data.get('email')
        if email:
            # Check if we processed this email FOR THIS JOB in the last 2 minutes
            existing = storage_service.get_recent_candidate_by_email(email, job_id=job_id, minutes=2)
            if existing:
                print(f"⚠️ DUPLICATE DETECTED: Ignoring webhook for {email} on job {job_id} (processed recently)")
                return jsonify({"status": "success", "message": "Duplicate application ignored."}), 200

        # 1. Save Pending Application IMMEDIATELY (Critical for Vercel)
        candidate_id = save_pending_application(data)
        
        # 2. Process Application
        # For Vercel/Serverless, we must process SYNCHRONOUSLY to ensure it finishes.
        # Background threads are often killed in serverless environments.
        base_url = request.url_root 
        
        if os.environ.get('VERCEL') or os.environ.get('RAILWAY_ENVIRONMENT'):
            print("Running in Serverless mode (Synchronous processing)")
            process_application_background(data, candidate_id, base_url)
        else:
            print("Running in Server mode (Background thread)")
            import threading
            thread = threading.Thread(target=process_application_background, args=(data, candidate_id, base_url))
            thread.start()
        
        return jsonify({"status": "success", "message": "Application received and processed."}), 200

    except Exception as e:
        print(f"Error in webhook: {e}")
        return jsonify({"status": "error", "message": str(e)}), 500

def save_pending_application(data):
    """Save raw application data immediately to prevent data loss on serverless"""
    try:
        name = data.get('name', 'Unknown Candidate')
        email = data.get('email', '')
        phone = data.get('phone', '')
        resume_url = data.get('resume_url')
        linkedin_url = data.get('linkedin_url', '')
        job_description = data.get('job_description', '')
        answers = data.get('answers', {})
        job_id = data.get('job_id')
        
        # Create a basic candidate object
        candidate_data = {
            'id': f"cand_{int(datetime.now().timestamp())}_{uuid.uuid4().hex[:8]}",
            'job_id': job_id,
            'name': name,
            'email': email,
            'phone': phone,
            'resume_url': resume_url,
            'linkedin_url': linkedin_url,
            'job_description': job_description,
            'answers': answers,
            'timestamp': datetime.now().isoformat(),
            'total_score': 0,
            'skills': [],
            'ai_analysis': {'summary': 'Processing Pending... (Refresh to update)'},
            'raw_data': data,
            'status': 'pending'
        }
        
        storage_service.save_candidate(candidate_data)
        print(f"Saved pending application: {candidate_data['id']}")
        return candidate_data['id']
    except Exception as e:
        print(f"Error saving pending application: {e}")
        return None

def process_application_background(data, candidate_id=None, base_url=None, skip_emails=False):
    """Process the application in the background to avoid timeouts
    
    Args:
        data: Application data dict
        candidate_id: Optional ID if updating existing candidate
        base_url: Base URL for links in emails
        skip_emails: If True, skip sending emails (used for reprocessing)
    """
    with app.app_context():
        try:
            name = data.get('name', 'Unknown Candidate')
            email = data.get('email', '')
            phone = data.get('phone', '')
            resume_url = data.get('resume_url')
            linkedin_url = data.get('linkedin_url', '')
            job_description = data.get('job_description', '')
            answers = data.get('answers', {})
            
            # 1. Get Resume Text
            resume_text = ""
            candidate_info = {
                "name": name,
                "email": email,
                "phone": phone,
                "linkedin_url": linkedin_url,
                "raw_text": ""
            }
            
            if candidate_id:
                candidate_info['id'] = candidate_id
            
            if data.get('job_id'):
                candidate_info['job_id'] = data.get('job_id')

            
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
                    # Hybrid approach: Try gdown first, then robust requests fallback
                    import gdown
                    
                    # Create a temporary file path
                    ext = '.pdf' # Default assumption
                    temp_filename = f"temp_download_{uuid.uuid4().hex}{ext}"
                    temp_path = os.path.join(app.config['UPLOAD_FOLDER'], temp_filename)
                    
                    print(f"Attempting download with gdown: {resume_url}")
                    response = None
                    
                    try:
                        # gdown handles the virus scan warning automatically
                        output_path = gdown.download(resume_url, temp_path, quiet=False, fuzzy=True)
                        
                        if output_path and os.path.exists(output_path):
                            print(f"gdown download successful: {output_path}")
                            
                            # Read content
                            with open(output_path, 'rb') as f:
                                file_content = f.read()
                            
                            # Clean up temp file
                            try:
                                os.remove(output_path)
                            except:
                                pass
                                
                            # Mock a response object
                            class MockResponse:
                                def __init__(self, content):
                                    self.content = content
                                    self.status_code = 200
                                    self.headers = {'Content-Type': 'application/pdf'} # Assume PDF
                                    self.cookies = {}
                            
                            response = MockResponse(file_content)
                    except Exception as gdown_error:
                        print(f"gdown failed: {gdown_error}")
                    
                    # Fallback if gdown failed or didn't return a file
                    if not response:
                        print("Falling back to requests with cookie handling...")
                        session = requests.Session()
                        response = session.get(resume_url, allow_redirects=True, timeout=30)
                        
                        # Check for Google Drive virus scan warning (HTML response)
                        if response.status_code == 200 and ('text/html' in response.headers.get('Content-Type', '').lower()):
                            # Try to find confirmation token
                            for key, value in response.cookies.items():
                                if key.startswith('download_warning'):
                                    # Retry with confirmation token
                                    print(f"Found Google Drive confirmation token: {value}")
                                    params = {'confirm': value}
                                    if 'id=' in resume_url:
                                        response = session.get(resume_url + f"&confirm={value}", allow_redirects=True, timeout=30)
                                    else:
                                        response = session.get(resume_url, params=params, allow_redirects=True, timeout=30)
                                    break
                    
                    print(f"Download status: {response.status_code}, Content-Type: {response.headers.get('Content-Type')}, Size: {len(response.content)} bytes")
                    
                    if response.status_code == 200:
                        # Check if we STILL got HTML instead of a file
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
                                parsed_info = resume_parser.parse_resume(file_path, filename)
                                
                                # Merge parsed info but PREFER form data for critical fields
                                # This prevents "Robotics AI" (from resume text) overwriting "Candidate Name" (from form)
                                candidate_info.update(parsed_info)
                                
                                # FORCE override with form data if available
                                if name and name != 'Unknown Candidate':
                                    candidate_info['name'] = name
                                if email:
                                    candidate_info['email'] = email
                                if phone:
                                    candidate_info['phone'] = phone
                                    
                                if 'raw_text' not in candidate_info or not candidate_info['raw_text']:
                                    candidate_info['raw_text'] = f"Resume parsing failed. Resume URL: {resume_url}"
                                resume_text = candidate_info.get('raw_text', '')
                                print(f"Successfully parsed resume: {len(resume_text)} characters")
                                
                                # Add file URL for frontend access
                                # In Vercel/Cloud, local files are ephemeral. Use original URL.
                                if os.environ.get('VERCEL') or os.environ.get('RAILWAY_ENVIRONMENT'):
                                    candidate_info['file_url'] = resume_url
                                else:
                                    candidate_info['file_url'] = f"/uploads/{unique_filename}"
                                
                                candidate_info['original_filename'] = filename
                                
                            except Exception as parse_error:
                                print(f"Error parsing resume: {parse_error}")
                                candidate_info['raw_text'] = f"Resume parsing error: {str(parse_error)}\nResume URL: {resume_url}"
                                resume_text = candidate_info['raw_text']
                                # Still provide file access even if parsing failed
                                if os.environ.get('VERCEL') or os.environ.get('RAILWAY_ENVIRONMENT'):
                                    candidate_info['file_url'] = resume_url
                                else:
                                    candidate_info['file_url'] = f"/uploads/{unique_filename}"
                                candidate_info['original_filename'] = filename
                            
                            # Do NOT remove file so it can be viewed later
                except Exception as e:
                    print(f"Error downloading/parsing resume: {e}")
                    # Fallback if download fails
                    candidate_info['raw_text'] = f"Resume URL: {resume_url}"
                    resume_text = candidate_info['raw_text']
                    # Ensure file_url is set so the user can still view it
                    candidate_info['file_url'] = resume_url
                    candidate_info['parsing_failed'] = True
            
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
            # Ensure we preserve the ID and job_id if they were passed
            if candidate_id:
                score_result['id'] = candidate_id
            
            # Preserve job_id from the original data
            if data.get('job_id'):
                score_result['job_id'] = data.get('job_id')
            
            # Mark as processed (not pending anymore) - prevents duplicate processing
            # Note: Kanban frontend maps 'processed' to 'applied' column for display
            score_result['status'] = 'processed'
                
            storage_service.save_candidate(score_result)
            print("Candidate saved successfully with status: processed")
            
            # 5. Send Emails (only if not skipped)
            if skip_emails:
                print("Skipping emails (reprocessing mode)")
            else:
                print("Sending notifications...")
                
                # Send Candidate Confirmation
                cand_email = score_result.get('candidate_email') or score_result.get('email')
                cand_name = score_result.get('candidate_name') or score_result.get('name')
                
                if cand_email:
                    email_service.send_candidate_confirmation(cand_email, cand_name)
                
                # Send Admin Notification
                email_service.send_admin_notification(score_result, base_url)
            
        except Exception as e:
            print(f"Error in background processing: {e}")


@app.route('/api/candidates', methods=['GET'])
def get_candidates():
    """Get all stored candidates"""
    candidates = storage_service.get_all_candidates()
    return jsonify({'candidates': candidates})


@app.route('/api/candidates/fix-orphans', methods=['POST'])
def fix_orphan_candidates():
    """Fix candidates with no job_id by assigning them to a job"""
    data = request.json or {}
    target_job_id = data.get('job_id')  # Optional: specify which job to assign to
    
    result = storage_service.fix_orphan_candidates(target_job_id)
    
    if 'error' in result:
        return jsonify({'success': False, **result}), 400
    return jsonify({'success': True, **result})


@app.route('/api/candidates', methods=['DELETE'])
def clear_candidates():
    """Clear all stored candidates"""
    storage_service.clear_candidates()
    return jsonify({'success': True})


@app.route('/api/candidates/<candidate_id>/status', methods=['POST'])
def update_candidate_status(candidate_id):
    """Update candidate status (applied, rejected, interview_scheduled)"""
    data = request.json
    new_status = data.get('status')
    
    if not new_status:
        return jsonify({'success': False, 'error': 'Status required'}), 400
        
    success = storage_service.update_status(candidate_id, new_status)
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to update status'}), 500

@app.route('/api/reject', methods=['POST'])
def reject_candidate():
    """Send rejection email to candidate"""
    data = request.json
    email = data.get('email')
    name = data.get('name')
    candidate_id = data.get('id') # Optional ID to update status
    
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
        
    success = email_service.send_rejection_email(email, name)
    
    # If ID provided, update status to rejected
    if success and candidate_id:
        storage_service.update_status(candidate_id, 'rejected')
        
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to send email. Check server logs.'}), 500

@app.route('/api/schedule', methods=['POST'])
def schedule_interview():
    """Send interview invitation email"""
    data = request.json
    email = data.get('email')
    name = data.get('name')
    candidate_id = data.get('id')
    interview_details = data.get('details', {})
    
    if not email:
        return jsonify({'success': False, 'error': 'Email required'}), 400
        
    success = email_service.send_interview_invitation(email, name, interview_details)
    
    if success and candidate_id:
        storage_service.update_status(candidate_id, 'interview_scheduled')
        
    if success:
        return jsonify({'success': True})
    else:
        return jsonify({'success': False, 'error': 'Failed to send email. Check server logs.'}), 500

@app.route('/api/process/<candidate_id>', methods=['POST'])
def process_candidate_manual(candidate_id):
    """Manually trigger processing for a pending candidate"""
    try:
        # 1. Get candidate from DB
        candidates = storage_service.get_all_candidates()
        candidate = next((c for c in candidates if c['id'] == candidate_id), None)
        
        if not candidate:
            return jsonify({'success': False, 'error': 'Candidate not found'}), 404
        
        # 2. Check if already processed (prevent double processing)
        current_status = candidate.get('status', '')
        if current_status == 'processed' or current_status == 'applied' or current_status == 'interview_scheduled' or current_status == 'rejected':
            print(f"Candidate {candidate_id} already processed (status: {current_status}), skipping.")
            return jsonify({'success': True, 'message': 'Candidate already processed', 'skipped': True})
        
        # Also check if we have a valid score already
        if candidate.get('total_score', 0) > 0 and candidate.get('ai_analysis') and not candidate.get('ai_analysis', {}).get('summary', '').startswith('Processing Pending'):
            print(f"Candidate {candidate_id} has valid score ({candidate.get('total_score')}), skipping reprocess.")
            # Update status to applied if it was stuck on pending
            storage_service.update_status(candidate_id, 'applied')
            return jsonify({'success': True, 'message': 'Candidate already has score', 'skipped': True})
            
        # 3. Re-construct data object from stored raw_data or fields
        data = candidate.get('raw_data') or {
            'name': candidate.get('name'),
            'email': candidate.get('email'),
            'phone': candidate.get('phone'),
            'resume_url': candidate.get('resume_url'),
            'job_description': candidate.get('job_description'),
            'answers': candidate.get('answers')
        }
        
        # 4. Run processing synchronously (since user clicked the button)
        # Pass skip_emails=True since emails were already sent on first process
        process_application_background(data, candidate_id, skip_emails=True)
        
        return jsonify({'success': True, 'message': 'Candidate processed successfully'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)}), 500


if __name__ == '__main__':
    import sys
    port = int(os.environ.get('PORT', 5000))
    
    # Always run with Ngrok for local development unless --no-ngrok is passed
    # User requested: "it should always start with ngrok in local deployment"
    if '--no-ngrok' not in sys.argv:
        try:
            from pyngrok import ngrok
            
            # Check for auth token in env
            auth_token = os.environ.get("NGROK_AUTH_TOKEN")
            if auth_token:
                ngrok.set_auth_token(auth_token)
            
            try:
                # Connect to the port
                public_url = ngrok.connect(port).public_url
                
                print("\n" + "="*60)
                print(f" 🚀 NGROK TUNNEL ESTABLISHED")
                print(f" Public URL: {public_url}")
                print(f" Webhook URL: {public_url}/api/webhook/application")
                print("="*60)
                print(" INSTRUCTIONS:")
                print(" 1. Copy the Webhook URL above.")
                print(" 2. Go to your Google Apps Script Editor.")
                print(" 3. Update the WEBHOOK_URL variable.")
                print(" 4. Save and Deploy as Web App again.")
                print("="*60 + "\n")
                
            except Exception as e:
                if "ERR_NGROK_4018" in str(e) or "authentication failed" in str(e):
                    print("\n" + "!"*60)
                    print(" NGROK AUTHENTICATION REQUIRED")
                    print("!"*60)
                    print(" Ngrok now requires a free account.")
                    print(" 1. Go to: https://dashboard.ngrok.com/signup")
                    print(" 2. Copy your Authtoken.")
                    print(" 3. Add NGROK_AUTH_TOKEN to your .env file")
                    print("-" * 60)
                else:
                    print(f"Error starting ngrok: {e}")
        
        except ImportError:
            print("pyngrok not installed. Please run: pip install pyngrok")
            
        # Run without debug mode when using ngrok to avoid double-reloader issues
        app.run(host='0.0.0.0', port=port, debug=False)
        
    else:
        # Standard Local Run (only if --no-ngrok is passed)
        print(f"Starting Flask server on port {port} (Ngrok disabled)...")
        app.run(host='0.0.0.0', port=port, debug=True)
