import os
import json
import requests
import threading
import time

# API URLs
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Default API key (Perplexity)
DEFAULT_PERPLEXITY_KEY = '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'

# Rate limiting for concurrent AI requests
_ai_lock = threading.Lock()
_last_ai_call = 0
_MIN_INTERVAL = 1.0  # Minimum 1 second between AI calls


def _rate_limit():
    """Ensure minimum interval between AI API calls to avoid rate limits"""
    global _last_ai_call
    with _ai_lock:
        now = time.time()
        elapsed = now - _last_ai_call
        if elapsed < _MIN_INTERVAL:
            time.sleep(_MIN_INTERVAL - elapsed)
        _last_ai_call = time.time()


def analyze_candidate_with_ai(resume_text, job_description, interview_answers=None, provider=None, api_key=None):
    """
    Analyze a candidate's fit for a job using AI.
    Returns a dictionary with pros, cons, and analysis.
    """
    # Determine provider from env if not specified
    if not provider:
        provider = os.environ.get('AI_PROVIDER', 'perplexity').lower()

    if not api_key:
        api_key = get_default_api_key(provider)
        
    if not api_key:
        return {
            "pros": ["AI analysis unavailable (no API key)"],
            "cons": ["AI analysis unavailable (no API key)"],
            "summary": "Could not perform AI analysis."
        }

    # Prepare the prompt
    answers_text = ""
    if interview_answers:
        answers_text = "\n\nCandidate's Interview Answers:\n"
        for q, a in interview_answers.items():
            answers_text += f"Q: {q}\nA: {a}\n"

    prompt = f"""
    You are an expert Senior Recruiter and Hiring Manager with 15+ years experience. Evaluate this candidate for the specific role described below.
    
    JOB TITLE & DESCRIPTION:
    {job_description[:3000]}
    
    CANDIDATE PROFILE (Resume & Answers):
    {resume_text[:3000]}
    {answers_text}
    
    Task: Perform a DEEP, CRITICAL analysis of the candidate's fit and EXTRACT structured data.
    
    IMPORTANT RULES:
    1. Assume all monetary values are in Indian Rupees (INR) unless explicitly stated otherwise.
    2. If the resume is unconventional (e.g., code, raw text), infer skills and experience from context.
    3. Analyze the "Candidate's Interview Answers" for signs of AI generation (e.g. overly perfect structure, robotic tone, lack of personal anecdotes, generic examples). Be lenient, only flag if obvious.
    4. Be VERY CRITICAL. Do not give high scores easily:
       - 90-100: Perfect match, rare unicorn candidate
       - 75-89: Strong match, minor gaps
       - 60-74: Decent match, some concerns
       - 40-59: Weak match, significant gaps
       - 0-39: Poor match, not recommended
    5. Look for RED FLAGS: job hopping (<1 year stints), gaps, inconsistencies, keyword stuffing, vague descriptions.
    6. Evaluate IMPACT over responsibility - did they BUILD, LEAD, IMPROVE, or just PARTICIPATE?
    7. Consider RECENCY - recent experience in relevant tech is more valuable.
    
    Provide a structured analysis in JSON format with the following keys:
    - "pros": List of 3-5 specific strengths directly relevant to the job requirements. Be specific with examples from their profile.
    - "cons": List of 3-5 specific gaps, weaknesses, or concerns relative to the job. Be honest and direct.
    - "summary": A professional executive summary of the candidate's fit (2-3 sentences). Include hiring recommendation (Strong Yes / Yes / Maybe / No / Strong No).
    - "score_adjustment": An integer between -20 and +20. Use this to fine-tune based on intangibles.
    - "red_flags": List of any concerning patterns (empty list if none). Examples: "4 jobs in 3 years", "No quantifiable achievements", "Skills listed but no project evidence".
    - "extracted_data": {{
        "skills": ["List", "of", "all", "technical", "skills", "found"],
        "skills_match_score": <number 0-100: How well do candidate's skills match job requirements? Consider depth, not just presence.>,
        "years_of_experience": <number or 0 if unknown>,
        "education_level": "PhD|Masters|Bachelors|Diploma|HighSchool|Unknown",
        "current_role": "Job Title or Unknown",
        "current_company": "Company Name or Unknown",
        "relevance_score": <number 0-100: How relevant is their RECENT experience to THIS specific job? Penalize heavily for keyword stuffing without project evidence.>,
        "culture_fit_score": <number 0-100: Based on communication style, values shown, teamwork indicators>,
        "technical_depth_score": <number 0-100: Junior (0-40), Mid (41-70), Senior (71-85), Staff/Principal (86-100). Look for evidence of IMPACT and COMPLEXITY, not just years.>,
        "leadership_score": <number 0-100: Evidence of mentoring, leading teams, driving initiatives. 0 if IC role.>,
        "communication_score": <number 0-100: Quality of writing in resume/answers. Clear, concise, professional?>,
        "project_complexity_score": <number 0-100: Did they work on complex, impactful projects or routine tasks?>,
        "growth_trajectory": "Rising|Stable|Declining|Unknown": Career progression pattern,
        "missing_must_haves": ["List", "of", "critical", "skills", "or", "requirements", "missing"],
        "nice_to_haves_present": ["List", "of", "bonus", "skills", "they", "have"],
        "ai_generated_probability": <number 0-100: Likelihood that INTERVIEW ANSWERS were AI-generated. 0=Human, 100=Definitely AI. Be conservative.>,
        "overall_recommendation": "Strong Hire|Hire|Maybe|No Hire|Strong No",
        "salary_expectation_fit": "Unknown|Below|Match|Above" based on their level vs typical role
    }}
    
    Return ONLY the JSON. No markdown, no explanation.
    """

    try:
        if provider == 'openai':
            return _call_openai_analysis(api_key, prompt)
        elif provider == 'claude':
            return _call_claude_analysis(api_key, prompt)
        else:
            return _call_perplexity_analysis(api_key, prompt)
            
    except Exception as e:
        print(f"AI Analysis Error: {e}")
        return {
            "pros": ["Error during AI analysis"],
            "cons": ["Error during AI analysis"],
            "summary": "AI analysis failed."
        }

def _call_perplexity_analysis(api_key, prompt):
    # Rate limit to prevent API overload on concurrent submissions
    _rate_limit()
    
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "sonar",
        "messages": [
            {"role": "system", "content": "You are a helpful HR assistant. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2
    }
    
    # Retry with exponential backoff for rate limits (important for serverless)
    max_retries = 3
    for attempt in range(max_retries):
        try:
            response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data, timeout=60)
            
            if response.status_code == 429:  # Rate limited
                wait_time = (2 ** attempt) + 1  # 1, 3, 5 seconds
                print(f"Rate limited, waiting {wait_time}s before retry...")
                time.sleep(wait_time)
                continue
                
            response.raise_for_status()
            result = response.json()
            content = result['choices'][0]['message']['content']
            return _parse_json_response(content)
            
        except requests.exceptions.Timeout:
            print(f"API timeout on attempt {attempt + 1}")
            if attempt < max_retries - 1:
                time.sleep(2)
                continue
            raise
        except requests.exceptions.RequestException as e:
            if attempt < max_retries - 1 and '429' in str(e):
                time.sleep(2 ** attempt)
                continue
            raise
    
    raise Exception("Max retries exceeded for Perplexity API")

def _call_openai_analysis(api_key, prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": os.environ.get('OPENAI_MODEL', 'gpt-4o'),
        "messages": [
            {"role": "system", "content": "You are a helpful HR assistant. Output only valid JSON."},
            {"role": "user", "content": prompt}
        ],
        "temperature": 0.2,
        "response_format": {"type": "json_object"}
    }
    
    response = requests.post(OPENAI_API_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    return _parse_json_response(content)

def _call_claude_analysis(api_key, prompt):
    headers = {
        "x-api-key": api_key,
        "anthropic-version": "2023-06-01",
        "content-type": "application/json"
    }
    data = {
        "model": os.environ.get('CLAUDE_MODEL', 'claude-3-5-sonnet-20240620'),
        "max_tokens": 1000,
        "messages": [
            {"role": "user", "content": prompt + "\n\nOutput JSON only."}
        ]
    }
    
    response = requests.post(CLAUDE_API_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    content = result['content'][0]['text']
    return _parse_json_response(content)

def _parse_json_response(content):
    try:
        # Clean up markdown code blocks if present
        if "```json" in content:
            content = content.split("```json")[1].split("```")[0]
        elif "```" in content:
            content = content.split("```")[1].split("```")[0]
        
        return json.loads(content.strip())
    except:
        return {
            "pros": ["Could not parse AI response"],
            "cons": ["Could not parse AI response"],
            "summary": "Raw output: " + content[:100] + "..."
        }

def get_default_api_key(provider):
    """Get default API key for a provider"""
    if provider == 'perplexity':
        return os.environ.get('PERPLEXITY_API_KEY', DEFAULT_PERPLEXITY_KEY)
    elif provider == 'openai':
        return os.environ.get('OPENAI_API_KEY', '')
    elif provider == 'claude':
        return os.environ.get('ANTHROPIC_API_KEY', '')
    return ''


def build_prompt(job_description, job_title, num_questions, question_types):
    """Build the prompt for generating interview questions"""
    type_instructions = ""
    if question_types == 'technical':
        type_instructions = "Focus strictly on technical skills, coding challenges, system design, and specific technologies mentioned in the job description."
    elif question_types == 'behavioral':
        type_instructions = "Focus strictly on behavioral questions using the STAR method (Situation, Task, Action, Result) to assess soft skills and past experiences."
    elif question_types == 'situational':
        type_instructions = "Focus strictly on hypothetical scenarios and situational judgment tests relevant to the role."
    else:  # mixed
        type_instructions = "Include a balanced mix of technical (40%), behavioral (30%), and situational (30%) questions."
    
    return f"""You are an expert HR professional and technical recruiter with 20 years of experience. 
Your task is to generate a set of exactly {num_questions} high-quality, challenging, and role-specific interview questions for the following position.

Job Title: {job_title}

Job Description:
{job_description}

Instructions:
1. Generate exactly {num_questions} questions.
2. {type_instructions}
3. Questions MUST be directly relevant to the specific requirements, tools, and responsibilities mentioned in the job description. Avoid generic questions.
4. For technical questions, include specific scenarios or problems to solve, not just definition questions.
5. For behavioral questions, look for specific examples of past performance.
6. Ensure a mix of difficulty levels, from fundamental concepts to advanced problem-solving.
7. The output MUST be valid JSON only.

Return the questions as a JSON array with the following structure:
[
    {{
        "question": "The interview question text",
        "category": "technical|behavioral|situational",
        "difficulty": "easy|medium|hard",
        "expected_skills": ["skill1", "skill2"],
        "evaluation_criteria": "Brief note on what a good answer should include"
    }}
]

Return ONLY the JSON array, no additional text, no markdown formatting, no explanations."""


def call_perplexity(prompt, api_key):
    """Call Perplexity API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": "sonar",
        "messages": [
            {
                "role": "system",
                "content": "You are an expert HR professional who creates insightful interview questions. Always respond with valid JSON only, no markdown code blocks or additional text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 3000,
        "temperature": 0.7
    }
    
    response = requests.post(PERPLEXITY_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content'].strip()


def call_openai(prompt, api_key):
    """Call OpenAI API"""
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    
    payload = {
        "model": os.environ.get('OPENAI_MODEL', 'gpt-4o'),
        "messages": [
            {
                "role": "system",
                "content": "You are an expert HR professional who creates insightful interview questions. Always respond with valid JSON only, no markdown code blocks or additional text."
            },
            {
                "role": "user",
                "content": prompt
            }
        ],
        "max_tokens": 3000,
        "temperature": 0.7
    }
    
    response = requests.post(OPENAI_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result['choices'][0]['message']['content'].strip()


def call_claude(prompt, api_key):
    """Call Claude (Anthropic) API"""
    headers = {
        "x-api-key": api_key,
        "Content-Type": "application/json",
        "anthropic-version": "2023-06-01"
    }
    
    payload = {
        "model": os.environ.get('CLAUDE_MODEL', 'claude-3-5-sonnet-20240620'),
        "max_tokens": 3000,
        "system": "You are an expert HR professional who creates insightful interview questions. Always respond with valid JSON only, no markdown code blocks or additional text.",
        "messages": [
            {
                "role": "user",
                "content": prompt
            }
        ]
    }
    
    response = requests.post(CLAUDE_API_URL, headers=headers, json=payload, timeout=60)
    response.raise_for_status()
    
    result = response.json()
    return result['content'][0]['text'].strip()


def parse_ai_response(content):
    """Parse AI response to extract JSON questions"""
    # Clean up the response if needed
    if content.startswith('```json'):
        content = content[7:]
    if content.startswith('```'):
        content = content[3:]
    if content.endswith('```'):
        content = content[:-3]
    content = content.strip()
    
    # Find JSON array in response
    start_idx = content.find('[')
    end_idx = content.rfind(']') + 1
    if start_idx != -1 and end_idx > start_idx:
        content = content[start_idx:end_idx]
    
    questions = json.loads(content)
    
    # Ensure each question has required fields
    for i, q in enumerate(questions):
        if 'question' not in q:
            continue
        if 'category' not in q:
            q['category'] = 'general'
        if 'difficulty' not in q:
            q['difficulty'] = 'medium'
        if 'expected_skills' not in q:
            q['expected_skills'] = []
        q['id'] = i + 1
    
    return questions


def generate_interview_questions(job_description, job_title, num_questions=10, question_types='mixed', ai_provider=None, custom_api_key=''):
    """Generate interview questions using the specified AI provider"""
    
    try:
        # Determine provider from env if not specified
        if not ai_provider:
            ai_provider = os.environ.get('AI_PROVIDER', 'perplexity').lower()

        # Get API key (use custom if provided, otherwise use default)
        api_key = custom_api_key if custom_api_key else get_default_api_key(ai_provider)
        
        if not api_key:
            print(f"No API key available for {ai_provider}")
            return generate_questions_fallback(job_description, job_title, num_questions, question_types)
        
        # Build the prompt
        prompt = build_prompt(job_description, job_title, num_questions, question_types)
        
        # Call the appropriate API
        print(f"Using AI provider: {ai_provider}")
        
        if ai_provider == 'openai':
            content = call_openai(prompt, api_key)
        elif ai_provider == 'claude':
            content = call_claude(prompt, api_key)
        else:  # default to perplexity
            content = call_perplexity(prompt, api_key)
        
        # Parse and return questions
        return parse_ai_response(content)
        
    except json.JSONDecodeError as e:
        print(f"Error parsing AI response: {str(e)}")
        return generate_questions_fallback(job_description, job_title, num_questions, question_types)
    except requests.exceptions.RequestException as e:
        print(f"API request error: {str(e)}")
        return generate_questions_fallback(job_description, job_title, num_questions, question_types)
    except Exception as e:
        print(f"Error generating questions: {str(e)}")
        return generate_questions_fallback(job_description, job_title, num_questions, question_types)


def generate_questions_fallback(job_description, job_title, num_questions=10, question_types='mixed'):
    """Generate questions using a template-based approach (fallback when API fails)"""
    
    keywords = extract_keywords(job_description)
    
    technical_questions = [
        {"question": f"Can you describe your experience with {keywords[0] if keywords else 'the technologies mentioned in the job description'}?", "category": "technical", "difficulty": "medium"},
        {"question": "Walk me through a challenging technical problem you solved recently.", "category": "technical", "difficulty": "hard"},
        {"question": f"How would you approach learning a new technology required for this {job_title} role?", "category": "technical", "difficulty": "easy"},
        {"question": "Describe your experience with version control and collaborative development.", "category": "technical", "difficulty": "medium"},
        {"question": f"What tools and technologies are you most proficient in that relate to this {job_title} position?", "category": "technical", "difficulty": "easy"},
    ]
    
    behavioral_questions = [
        {"question": "Tell me about a time when you had to meet a tight deadline. How did you handle it?", "category": "behavioral", "difficulty": "medium"},
        {"question": "Describe a situation where you had to work with a difficult team member.", "category": "behavioral", "difficulty": "medium"},
        {"question": "Give an example of a time you took initiative on a project.", "category": "behavioral", "difficulty": "easy"},
        {"question": "Tell me about a failure you experienced and what you learned from it.", "category": "behavioral", "difficulty": "hard"},
        {"question": "Describe a time when you had to adapt to a significant change at work.", "category": "behavioral", "difficulty": "medium"},
    ]
    
    situational_questions = [
        {"question": f"If you were hired as {job_title}, what would be your first priorities?", "category": "situational", "difficulty": "medium"},
        {"question": "How would you handle a situation where you disagree with your manager's decision?", "category": "situational", "difficulty": "medium"},
        {"question": "What would you do if you realized you couldn't complete a task by the deadline?", "category": "situational", "difficulty": "easy"},
        {"question": "How would you prioritize multiple urgent tasks?", "category": "situational", "difficulty": "hard"},
        {"question": "If a colleague asked for help but you were busy with your own work, how would you handle it?", "category": "situational", "difficulty": "easy"},
    ]
    
    if question_types == 'technical':
        base_questions = technical_questions * 3
    elif question_types == 'behavioral':
        base_questions = behavioral_questions * 3
    elif question_types == 'situational':
        base_questions = situational_questions * 3
    else:
        base_questions = technical_questions + behavioral_questions + situational_questions
    
    questions = []
    for i, q in enumerate(base_questions[:num_questions]):
        q_copy = q.copy()
        q_copy['id'] = i + 1
        q_copy['expected_skills'] = keywords[:3] if keywords else []
        questions.append(q_copy)
    
    return questions


def format_job_description(text, provider=None, api_key=None):
    """
    Format a raw job description into structured HTML using AI.
    """
    if not text:
        return ""
        
    # Determine provider from env if not specified
    if not provider:
        provider = os.environ.get('AI_PROVIDER', 'perplexity').lower()

    if not api_key:
        api_key = get_default_api_key(provider)
        
    if not api_key:
        return text # Return original if no AI available

    prompt = f"""
    You are a professional editor. Format the following job description into clean, structured HTML for a web display.
    
    Rules:
    1. Use <h3> for section headers (e.g., "Responsibilities", "Requirements", "About Us").
    2. Use <ul> and <li> for lists.
    3. Use <p> for paragraphs.
    4. Use <strong> for key terms if appropriate.
    5. Do NOT change the actual content/words, only the structure and formatting.
    6. Do NOT include <html>, <head>, or <body> tags. Just the content.
    7. Return a JSON object with a single key "html" containing the HTML string.
    
    Job Description:
    {text[:5000]}
    """

    try:
        if provider == 'openai':
            content = _call_openai_analysis(api_key, prompt)
        elif provider == 'claude':
            content = _call_claude_analysis(api_key, prompt)
        else:
            content = _call_perplexity_analysis(api_key, prompt)
            
        # Handle response
        if isinstance(content, dict):
            if 'html' in content:
                return content['html']
            elif 'content' in content:
                return content['content']
            # If we got the error dict from _parse_json_response
            elif 'pros' in content and isinstance(content['pros'], list) and 'Could not parse' in content['pros'][0]:
                return text
            else:
                # Fallback: return original text if we can't find the HTML
                return text
        
        return str(content)
            
    except Exception as e:
        print(f"Error formatting job description: {e}")
        return text


def extract_keywords(text):
    """Extract potential keywords/skills from job description"""
    common_skills = [
        'python', 'javascript', 'java', 'react', 'node', 'sql', 'aws', 'docker',
        'kubernetes', 'machine learning', 'data analysis', 'project management',
        'communication', 'leadership', 'agile', 'scrum', 'git', 'api', 'rest',
        'html', 'css', 'typescript', 'angular', 'vue', 'mongodb', 'postgresql',
        'excel', 'salesforce', 'marketing', 'sales', 'customer service',
        'c++', 'c#', '.net', 'azure', 'gcp', 'devops', 'ci/cd', 'testing'
    ]
    
    text_lower = text.lower()
    found_skills = [skill for skill in common_skills if skill in text_lower]
    
    return found_skills[:10] if found_skills else ['relevant skills']
