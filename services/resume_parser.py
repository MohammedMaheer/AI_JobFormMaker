"""
Resume Parser - Extract information from candidate resumes
"""
import re
from typing import Dict, List, Optional
from datetime import datetime
from .file_processor import extract_text_from_file

class ResumeParser:
    def __init__(self):
        # Comprehensive list of skills
        self.skill_keywords = {
            'Programming Languages': [
                'python', 'java', 'javascript', 'typescript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
                'go', 'golang', 'rust', 'scala', 'perl', 'r', 'matlab', 'assembly', 'shell', 'bash'
            ],
            'Web Frameworks': [
                'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring', 'asp.net', 'laravel',
                'ruby on rails', 'express', 'fastapi', 'next.js', 'nuxt.js', 'svelte', 'jquery', 'bootstrap', 'tailwind'
            ],
            'Databases': [
                'sql', 'mysql', 'postgresql', 'mongodb', 'redis', 'elasticsearch', 'oracle', 'sql server',
                'sqlite', 'cassandra', 'dynamodb', 'mariadb', 'neo4j', 'firebase'
            ],
            'Cloud & DevOps': [
                'aws', 'azure', 'gcp', 'google cloud', 'docker', 'kubernetes', 'jenkins', 'git', 'github', 'gitlab',
                'ci/cd', 'terraform', 'ansible', 'puppet', 'chef', 'linux', 'unix', 'nginx', 'apache', 'heroku'
            ],
            'AI & Data Science': [
                'machine learning', 'deep learning', 'artificial intelligence', 'data science', 'tensorflow', 'pytorch',
                'keras', 'scikit-learn', 'pandas', 'numpy', 'opencv', 'nlp', 'computer vision', 'big data', 'hadoop', 'spark'
            ],
            'Mobile': [
                'android', 'ios', 'react native', 'flutter', 'xamarin', 'ionic', 'swiftui'
            ],
            'Soft Skills': [
                'leadership', 'communication', 'teamwork', 'problem solving', 'critical thinking',
                'project management', 'agile', 'scrum', 'time management', 'adaptability', 'collaboration'
            ]
        }

    def parse_resume(self, file_path: str, filename: str) -> Dict:
        """Parse resume and extract key information"""
        try:
            text = extract_text_from_file(file_path)
        except Exception as e:
            print(f"Error extracting text: {e}")
            text = ""
        
        if not text:
            return {"error": "Could not extract text from resume"}
        
        # Clean text
        clean_text = self._clean_text(text)
        
        # Extract information
        info = {
            "raw_text": text,
            "name": self._extract_name(clean_text, filename),
            "email": self._extract_email(clean_text),
            "phone": self._extract_phone(clean_text),
            "skills": self._extract_skills(clean_text),
            "education": self._extract_education(clean_text),
            "experience_years": self._extract_experience_years(clean_text),
            "certifications": self._extract_certifications(clean_text),
            "languages": self._extract_languages(clean_text),
            "summary": self._extract_summary(clean_text)
        }
        
        return info

    def _clean_text(self, text: str) -> str:
        """Clean and normalize text"""
        # Remove multiple spaces
        text = re.sub(r'\s+', ' ', text)
        # Remove special characters but keep punctuation useful for parsing
        text = re.sub(r'[^\w\s.,@\-+():/]', '', text)
        return text.strip()
    
    def _extract_name(self, text: str, filename: str) -> Optional[str]:
        """Extract candidate name"""
        # Strategy 1: Check filename if it looks like a name
        base_name = filename.rsplit('.', 1)[0].replace('_', ' ').replace('-', ' ')
        
        # Skip filename strategy if it contains generic terms
        is_generic_filename = any(term in base_name.lower() for term in ['resume', 'cv', 'curriculum', 'vitae'])
        
        if not is_generic_filename and re.match(r'^[A-Za-z ]+$', base_name) and len(base_name.split()) >= 2:
            return base_name.title()

        # Strategy 2: First few words of the resume
        # Exclude common headers
        common_headers = ['resume', 'cv', 'curriculum', 'vitae', 'profile', 'summary', 'contact']
        words = text.split()[:10]
        potential_name = []
        
        for word in words:
            if word.lower() in common_headers:
                continue
            if word[0].isupper() and word.isalpha():
                potential_name.append(word)
                if len(potential_name) >= 2:
                    break
            elif potential_name: # Stop if we hit a non-name word after finding some name words
                break
                
        if potential_name:
            return ' '.join(potential_name)
            
        return "Unknown Candidate"
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        # More robust phone patterns
        phone_patterns = [
            r'(?:\+\d{1,3}[-.\s]?)?\(?\d{3}\)?[-.\s]?\d{3}[-.\s]?\d{4}',  # US/General
            r'(?:\+\d{1,3}[-.\s]?)?\d{10,12}',  # International simple
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                # Filter out things that look like dates (e.g. 2020-2021)
                valid_matches = [m for m in matches if not re.match(r'20\d{2}.20\d{2}', m)]
                if valid_matches:
                    return valid_matches[0].strip()
        return None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical and soft skills"""
        text_lower = text.lower()
        found_skills = set()
        
        for category, skills in self.skill_keywords.items():
            for skill in skills:
                # Use word boundary to avoid partial matches (e.g., "go" in "good")
                if re.search(r'\b' + re.escape(skill) + r'\b', text_lower):
                    found_skills.add(skill.title()) # Capitalize for display
                    
        return list(found_skills)
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        text_lower = text.lower()
        
        # Degree patterns
        degree_patterns = {
            'PhD': [r'ph\.?d\.?', r'doctorate', r'doctor of philosophy'],
            'Master': [r'master', r'm\.?s\.?', r'm\.?a\.?', r'm\.?b\.?a\.?', r'm\.?tech'],
            'Bachelor': [r'bachelor', r'b\.?s\.?', r'b\.?a\.?', r'b\.?tech', r'b\.?e\.?'],
            'Associate': [r'associate']
        }
        
        # Try to find sentences or lines containing degree info
        lines = text.split('\n') # Use original text for lines? No, clean_text is single line mostly if we stripped newlines.
        # Let's use a window approach on the text
        
        for degree_type, patterns in degree_patterns.items():
            for pattern in patterns:
                matches = re.finditer(r'\b' + pattern + r'\b', text_lower)
                for match in matches:
                    # Extract context (e.g., 50 chars before and after)
                    start = max(0, match.start() - 50)
                    end = min(len(text), match.end() + 100)
                    context = text[start:end]
                    
                    # Check if we already have this degree type
                    if not any(e['degree'] == degree_type for e in education):
                        education.append({
                            'degree': degree_type,
                            'details': context.strip()
                        })
        
        return education
    
    def _extract_experience_years(self, text: str) -> float:
        """Extract years of experience"""
        # 1. Look for explicit mentions
        explicit_patterns = [
            r'(\d+(?:\.\d+)?)\+?\s*years?(?:\s+of)?\s+experience',
            r'experience\s*:?\s*(\d+(?:\.\d+)?)\+?\s*years?'
        ]
        
        for pattern in explicit_patterns:
            match = re.search(pattern, text.lower())
            if match:
                try:
                    return float(match.group(1))
                except:
                    pass

        # 2. Calculate from dates (heuristic)
        # Look for year ranges like 2015 - 2020 or 2015 - Present
        year_pattern = r'(19|20)\d{2}'
        years = re.findall(year_pattern, text)
        if years:
            years = [int(y) for y in years]
            if years:
                min_year = min(years)
                max_year = datetime.now().year
                # If "Present" or "Current" is found near a date, assume until now
                if "present" in text.lower() or "current" in text.lower():
                    pass # max_year is already now
                else:
                    max_year = max(years)
                
                span = max_year - min_year
                # Cap at reasonable number (e.g. 40) to avoid parsing birth years etc.
                if 0 < span < 50:
                    return float(span)
        
        return 0.0
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        text_lower = text.lower()
        
        common_certs = [
            'aws certified', 'azure certified', 'google cloud certified',
            'pmp', 'cissp', 'comptia', 'ccna', 'ccnp',
            'certified scrum master', 'csm', 'cka', 'ckad',
            'tensorflow developer', 'oracle certified', 'oscp', 'ceh'
        ]
        
        found_certs = []
        for cert in common_certs:
            if cert in text_lower:
                found_certs.append(cert.title())
        
        return found_certs
    
    def _extract_languages(self, text: str) -> List[str]:
        """Extract spoken languages"""
        text_lower = text.lower()
        
        languages = ['english', 'spanish', 'french', 'german', 'chinese', 'japanese', 
                    'korean', 'arabic', 'hindi', 'portuguese', 'russian', 'italian', 'dutch']
        
        found_languages = []
        for lang in languages:
            if lang in text_lower:
                found_languages.append(lang.title())
        
        return found_languages
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary"""
        # Look for keywords that start a summary section
        summary_keywords = ['summary', 'professional summary', 'profile', 'about me', 'objective']
        text_lower = text.lower()
        
        for keyword in summary_keywords:
            idx = text_lower.find(keyword)
            if idx != -1:
                # Extract next 300 chars
                start = idx + len(keyword)
                return text[start:start+300].strip() + "..."
                
        # Fallback: First 200 chars
        return text[:200].strip() + "..."
