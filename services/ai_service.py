import os
import json
import requests

# API URLs
PERPLEXITY_API_URL = "https://api.perplexity.ai/chat/completions"
OPENAI_API_URL = "https://api.openai.com/v1/chat/completions"
CLAUDE_API_URL = "https://api.anthropic.com/v1/messages"

# Default API key (Perplexity)
DEFAULT_PERPLEXITY_KEY = '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'


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
        type_instructions = "Focus on technical skills, coding problems, and technical knowledge."
    elif question_types == 'behavioral':
        type_instructions = "Focus on behavioral questions using STAR method (Situation, Task, Action, Result)."
    elif question_types == 'situational':
        type_instructions = "Focus on hypothetical situational questions."
    else:  # mixed
        type_instructions = "Include a mix of technical, behavioral, and situational questions."
    
    return f"""You are an expert HR professional and interview specialist. Based on the following job description, generate exactly {num_questions} interview questions that would help assess candidates for this role.

Job Title: {job_title}

Job Description:
{job_description}

Instructions:
1. {type_instructions}
2. Questions should be relevant to the specific requirements mentioned in the job description.
3. Include questions that assess both hard skills and soft skills.
4. Make questions clear, professional, and open-ended.
5. Vary the difficulty level from basic to advanced.

Return the questions as a JSON array with the following structure:
[
    {{
        "question": "The interview question",
        "category": "technical|behavioral|situational",
        "difficulty": "easy|medium|hard",
        "expected_skills": ["skill1", "skill2"]
    }}
]

Return ONLY the JSON array, no additional text or markdown formatting."""


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
