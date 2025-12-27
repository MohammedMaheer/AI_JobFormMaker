"""
Resume Parser - Extract information from candidate resumes
"""
import re
from typing import Dict, List, Optional
from .file_processor import extract_text_from_file

class ResumeParser:
    def __init__(self):
        pass
        
    def parse_resume(self, file_path: str, filename: str) -> Dict:
        """Parse resume and extract key information"""
        # Extract text from file
        try:
            text = extract_text_from_file(file_path)
        except Exception as e:
            print(f"Error extracting text: {e}")
            text = ""
        
        if not text:
            return {"error": "Could not extract text from resume"}
        
        # Extract information
        info = {
            "raw_text": text,
            "name": self._extract_name(text),
            "email": self._extract_email(text),
            "phone": self._extract_phone(text),
            "skills": self._extract_skills(text),
            "education": self._extract_education(text),
            "experience_years": self._extract_experience_years(text),
            "certifications": self._extract_certifications(text),
            "languages": self._extract_languages(text),
            "summary": self._extract_summary(text)
        }
        
        return info
    
    def _extract_name(self, text: str) -> Optional[str]:
        """Extract candidate name (usually in first few lines)"""
        lines = text.strip().split('\n')
        # First non-empty line is often the name
        for line in lines[:5]:
            line = line.strip()
            if line and len(line) < 50 and not '@' in line:
                # Simple heuristic: name is short and doesn't contain email
                return line
        return None
    
    def _extract_email(self, text: str) -> Optional[str]:
        """Extract email address"""
        email_pattern = r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b'
        matches = re.findall(email_pattern, text)
        return matches[0] if matches else None
    
    def _extract_phone(self, text: str) -> Optional[str]:
        """Extract phone number"""
        phone_patterns = [
            r'\+?1?\s*\(?([0-9]{3})\)?[-.\s]?([0-9]{3})[-.\s]?([0-9]{4})',
            r'\b\d{10}\b',
            r'\+\d{1,3}\s?\d{8,12}'
        ]
        
        for pattern in phone_patterns:
            matches = re.findall(pattern, text)
            if matches:
                if isinstance(matches[0], tuple):
                    return ''.join(matches[0])
                return matches[0]
        return None
    
    def _extract_skills(self, text: str) -> List[str]:
        """Extract technical and soft skills"""
        text_lower = text.lower()
        
        # Common technical skills
        technical_skills = [
            'python', 'java', 'javascript', 'c++', 'c#', 'ruby', 'php', 'swift', 'kotlin',
            'react', 'angular', 'vue', 'node.js', 'django', 'flask', 'spring',
            'sql', 'nosql', 'mongodb', 'postgresql', 'mysql', 'redis',
            'aws', 'azure', 'gcp', 'docker', 'kubernetes', 'jenkins', 'git',
            'machine learning', 'deep learning', 'ai', 'data science', 'tensorflow', 'pytorch',
            'html', 'css', 'rest api', 'graphql', 'microservices', 'agile', 'scrum',
            'linux', 'unix', 'windows server', 'networking', 'security', 'devops'
        ]
        
        # Soft skills
        soft_skills = [
            'leadership', 'communication', 'teamwork', 'problem solving',
            'critical thinking', 'project management', 'collaboration', 'adaptability'
        ]
        
        all_skills = technical_skills + soft_skills
        found_skills = []
        
        for skill in all_skills:
            if skill in text_lower:
                found_skills.append(skill.title())
        
        return list(set(found_skills))  # Remove duplicates
    
    def _extract_education(self, text: str) -> List[Dict]:
        """Extract education information"""
        education = []
        text_lower = text.lower()
        
        # Look for degree keywords
        degrees = ['phd', 'ph.d', 'doctorate', 'master', 'mba', 'bachelor', 'associate', 'b.s', 'b.a', 'm.s', 'm.a', 'b.tech', 'm.tech']
        
        for degree in degrees:
            if degree in text_lower:
                education.append({
                    'degree': degree.upper(),
                    'field': 'Not specified'
                })
        
        return education
    
    def _extract_experience_years(self, text: str) -> Optional[float]:
        """Extract years of experience"""
        # Look for patterns like "5 years", "5+ years", "5-7 years"
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'experience[:\s]+(\d+)\+?\s*years?',
            r'(\d+)\+?\s*years?\s+in'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, text.lower())
            if matches:
                try:
                    return float(matches[0])
                except:
                    pass
        
        return None
    
    def _extract_certifications(self, text: str) -> List[str]:
        """Extract certifications"""
        text_lower = text.lower()
        
        common_certs = [
            'aws certified', 'azure certified', 'google cloud certified',
            'pmp', 'cissp', 'comptia', 'ccna', 'ccnp',
            'certified scrum master', 'csm', 'cka', 'ckad',
            'tensorflow developer', 'oracle certified'
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
                    'korean', 'arabic', 'hindi', 'portuguese', 'russian', 'italian']
        
        found_languages = []
        for lang in languages:
            if lang in text_lower:
                found_languages.append(lang.title())
        
        return found_languages
    
    def _extract_summary(self, text: str) -> str:
        """Extract professional summary or first few lines"""
        lines = text.strip().split('\n')
        
        # Look for summary section
        summary_keywords = ['summary', 'profile', 'objective', 'about']
        
        for i, line in enumerate(lines):
            if any(keyword in line.lower() for keyword in summary_keywords):
                # Get next few lines
                summary_lines = lines[i+1:i+5]
                return ' '.join([l.strip() for l in summary_lines if l.strip()])
        
        # If no summary section, return first paragraph
        for line in lines[:10]:
            if len(line) > 50:
                return line.strip()
        
        return "No summary available"
