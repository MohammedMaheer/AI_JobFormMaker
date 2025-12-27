import os
import json
import requests

# API URLs
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Default API key (Perplexity)
DEFAULT_PERPLEXITY_KEY = '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'


def analyze_candidate_with_ai(resume_text, job_description, interview_answers=None, provider='perplexity', api_key=None):
    """
    Analyze a candidate's fit for a job using AI.
    Returns a dictionary with pros, cons, and analysis.
    """
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
    You are an expert Senior Recruiter and Hiring Manager. Evaluate this candidate for the specific role described below.
    
    JOB TITLE & DESCRIPTION:
    {job_description[:3000]}
    
    CANDIDATE PROFILE (Resume & Answers):
    {resume_text[:3000]}
    {answers_text}
    
    Task: Perform a deep analysis of the candidate's fit and EXTRACT structured data.
    
    IMPORTANT: 
    1. Assume all monetary values are in Indian Rupees (INR) unless explicitly stated otherwise.
    2. If the resume is unconventional (e.g., code, raw text), infer skills and experience from context.
    
    Provide a structured analysis in JSON format with the following keys:
    - "pros": List of 3-5 specific strengths directly relevant to the job requirements.
    - "cons": List of 3-5 specific gaps, weaknesses, or missing skills relative to the job.
    - "summary": A professional executive summary of the candidate's fit (2-3 sentences).
    - "score_adjustment": An integer between -15 and +15.
    - "extracted_data": {{
        "skills": ["List", "of", "all", "technical", "skills", "found"],
        "years_of_experience": <number or 0 if unknown>,
        "education_level": "PhD|Masters|Bachelors|Unknown",
        "current_role": "Job Title or Unknown"
    }}
    
    Return ONLY the JSON.
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
    
    response = requests.post(PERPLEXITY_API_URL, headers=headers, json=data)
    response.raise_for_status()
    result = response.json()
    content = result['choices'][0]['message']['content']
    return _parse_json_response(content)

def _call_openai_analysis(api_key, prompt):
    headers = {
        "Authorization": f"Bearer {api_key}",
        "Content-Type": "application/json"
    }
    data = {
        "model": "gpt-4o-mini",
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
        "model": "claude-3-haiku-20240307",
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
        "model": "gpt-4o-mini",
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
        "model": "claude-3-haiku-20240307",
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


def generate_interview_questions(job_description, job_title, num_questions=10, question_types='mixed', ai_provider='perplexity', custom_api_key=''):
    """Generate interview questions using the specified AI provider"""
    
    try:
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
