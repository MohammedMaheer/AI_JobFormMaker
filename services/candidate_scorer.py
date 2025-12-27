"""
Candidate Scorer - Score and rank candidates based on job requirements
"""
from typing import Dict, List
import re

class CandidateScorer:
    def __init__(self):
        self.weights = {
            'skills_match': 0.35,
            'experience': 0.25,
            'education': 0.20,
            'keywords': 0.15,
            'certifications': 0.05
        }
    
    def score_candidate(self, candidate_info: Dict, job_description: str, job_title: str, ai_analysis: Dict = None) -> Dict:
        """Score a candidate against job requirements"""
        
        # If AI analysis is not provided, try to generate it on the fly if we have an API key
        # This makes the system more robust by ensuring AI insights are always attempted
        if not ai_analysis:
            try:
                from services.ai_service import analyze_candidate_with_ai
                # We import here to avoid circular imports
                ai_analysis = analyze_candidate_with_ai(
                    candidate_info.get('raw_text', ''), 
                    job_description
                )
            except Exception as e:
                print(f"Auto-AI analysis failed: {e}")

        # Merge AI extracted data if available to improve scoring accuracy
        if ai_analysis and 'extracted_data' in ai_analysis:
            extracted = ai_analysis['extracted_data']
            
            # Merge skills from AI and Regex
            ai_skills = extracted.get('skills', [])
            if ai_skills:
                # Normalize and merge
                current_skills = set(s.lower() for s in candidate_info.get('skills', []))
                for s in ai_skills:
                    current_skills.add(s.lower())
                # Convert back to title case for display
                candidate_info['skills'] = [s.title() for s in current_skills]
                
            # Update experience if AI found it
            if extracted.get('years_of_experience') is not None:
                try:
                    # Only update if we didn't find it or AI found more specific info
                    if candidate_info.get('experience_years') is None or candidate_info.get('experience_years') == 0:
                        candidate_info['experience_years'] = float(extracted['years_of_experience'])
                except:
                    pass
            
            # Update education if AI found it
            if extracted.get('education_level') and extracted['education_level'] != 'Unknown':
                # If we have no education data, use AI's finding
                if not candidate_info.get('education'):
                    candidate_info['education'] = [{'degree': extracted['education_level']}]

        scores = {
            'skills_match': self._score_skills(candidate_info.get('skills', []), job_description),
            'experience': self._score_experience(candidate_info.get('experience_years'), job_description),
            'education': self._score_education(candidate_info.get('education', []), job_description),
            'keywords': self._score_keywords(candidate_info.get('raw_text', ''), job_description),
            'certifications': self._score_certifications(candidate_info.get('certifications', []), job_description)
        }
        
        # Calculate weighted total
        total_score = sum(scores[key] * self.weights[key] for key in scores)
        
        # Apply AI adjustment if available
        ai_adjustment = 0
        if ai_analysis and 'score_adjustment' in ai_analysis:
            try:
                ai_adjustment = float(ai_analysis['score_adjustment'])
                # Clamp adjustment to reasonable range (-15 to +15)
                ai_adjustment = max(-15.0, min(15.0, ai_adjustment))
                total_score += ai_adjustment
            except:
                pass
        
        # Ensure score is within 0-100
        total_score = max(0.0, min(100.0, total_score))
        
        # Generate feedback
        feedback = self._generate_feedback(scores, candidate_info)
        
        result = {
            'total_score': round(total_score, 2),
            'breakdown': {k: round(v, 2) for k, v in scores.items()},
            'feedback': feedback,
            'grade': self._get_grade(total_score),
            'candidate_name': candidate_info.get('name', 'Unknown'),
            'candidate_email': candidate_info.get('email', 'N/A'),
            'candidate_phone': candidate_info.get('phone', 'N/A'),
            'file_url': candidate_info.get('file_url', '')
        }
        
        # Add AI insights if available
        if ai_analysis:
            result['ai_analysis'] = {
                'pros': ai_analysis.get('pros', []),
                'cons': ai_analysis.get('cons', []),
                'summary': ai_analysis.get('summary', ''),
                'adjustment': ai_adjustment
            }
            
        return result
    
    def _score_skills(self, candidate_skills: List[str], job_description: str) -> float:
        """Score based on skill match (0-100)"""
        if not candidate_skills:
            return 0.0
        
        job_desc_lower = job_description.lower()
        matched_skills = []
        
        # Common variations mapping
        variations = {
            'js': ['javascript'],
            'ts': ['typescript'],
            'py': ['python'],
            'cpp': ['c++'],
            'c#': ['csharp', 'c sharp'],
            'ml': ['machine learning'],
            'ai': ['artificial intelligence'],
            'dl': ['deep learning'],
            'fe': ['frontend', 'front-end'],
            'be': ['backend', 'back-end'],
            'fs': ['fullstack', 'full-stack'],
            'react': ['reactjs', 'react.js'],
            'node': ['nodejs', 'node.js'],
            'vue': ['vuejs', 'vue.js']
        }
        
        for skill in candidate_skills:
            skill_lower = skill.lower()
            
            # Direct match
            if skill_lower in job_desc_lower:
                matched_skills.append(skill)
                continue
                
            # Check variations
            if skill_lower in variations:
                found_var = False
                for var in variations[skill_lower]:
                    if var in job_desc_lower:
                        matched_skills.append(skill)
                        found_var = True
                        break
                if found_var:
                    continue
            
            # Check if skill is a variation of something in JD
            # e.g. skill="JavaScript", JD="JS"
            # We iterate over variations map to see if skill is a value
            for short, longs in variations.items():
                if skill_lower in longs:
                    if short in job_desc_lower.split(): # Use split to match whole word "js" not "json"
                        matched_skills.append(skill)
                        break

        if not matched_skills:
            return 0.0
            
        # Scoring Logic:
        # Instead of penalizing for extra skills (precision), we reward for finding relevant skills (recall-ish).
        # We assume finding ~5 relevant skills is a "good" match (100%).
        # We also give a small bonus for the ratio to encourage relevance.
        
        count_score = min(len(matched_skills) * 20.0, 100.0) # 5 skills = 100%
        
        return count_score
    
    def _score_experience(self, years: float, job_description: str) -> float:
        """Score based on experience (0-100)"""
        if years is None:
            return 50.0  # Neutral score if not specified
        
        # Extract required years from job description
        required_years = self._extract_required_years(job_description)
        
        if required_years is None:
            # No specific requirement, score based on general experience
            if years < 1:
                return 40.0
            elif years < 3:
                return 60.0
            elif years < 5:
                return 75.0
            elif years < 10:
                return 90.0
            else:
                return 100.0
        
        # Score based on how close to required
        if years >= required_years:
            return 100.0
        elif years >= required_years * 0.75:
            return 80.0
        elif years >= required_years * 0.5:
            return 60.0
        else:
            return 40.0
    
    def _score_education(self, education: List[Dict], job_description: str) -> float:
        """Score based on education (0-100)"""
        if not education:
            return 50.0  # Neutral score
        
        job_desc_lower = job_description.lower()
        
        # Check for degree requirements
        has_phd = any('phd' in e.get('degree', '').lower() for e in education)
        has_masters = any('master' in e.get('degree', '').lower() or 'mba' in e.get('degree', '').lower() for e in education)
        has_bachelors = any('bachelor' in e.get('degree', '').lower() or 'b.' in e.get('degree', '').lower() for e in education)
        
        if 'phd' in job_desc_lower or 'doctorate' in job_desc_lower:
            return 100.0 if has_phd else (80.0 if has_masters else 60.0)
        elif 'master' in job_desc_lower or 'mba' in job_desc_lower:
            return 100.0 if has_masters else (90.0 if has_phd else 70.0)
        elif 'bachelor' in job_desc_lower or 'degree' in job_desc_lower:
            return 100.0 if (has_bachelors or has_masters or has_phd) else 60.0
        else:
            # No specific requirement
            if has_phd:
                return 100.0
            elif has_masters:
                return 90.0
            elif has_bachelors:
                return 80.0
            else:
                return 70.0
    
    def _score_keywords(self, resume_text: str, job_description: str) -> float:
        """Score based on keyword match (0-100)"""
        resume_lower = resume_text.lower()
        job_lower = job_description.lower()
        
        # Extract important keywords from job description (nouns/verbs)
        # Simple approach: look for words that appear in both
        job_words = set(re.findall(r'\b\w{4,}\b', job_lower))
        resume_words = set(re.findall(r'\b\w{4,}\b', resume_lower))
        
        # Remove common words
        common_words = {'will', 'work', 'with', 'have', 'this', 'that', 'from', 'they', 'been', 'were', 'your', 'their'}
        job_words = job_words - common_words
        resume_words = resume_words - common_words
        
        if not job_words:
            return 50.0
        
        matches = job_words.intersection(resume_words)
        match_ratio = len(matches) / len(job_words)
        
        return min(100.0, match_ratio * 150)  # Can get bonus points
    
    def _score_certifications(self, certifications: List[str], job_description: str) -> float:
        """Score based on certifications (0-100)"""
        if not certifications:
            return 50.0
        
        job_desc_lower = job_description.lower()
        
        # Check if any certification is mentioned in job description
        relevant_certs = [cert for cert in certifications if cert.lower() in job_desc_lower]
        
        if relevant_certs:
            return 100.0
        elif certifications:
            return 75.0  # Has certifications, even if not specifically mentioned
        else:
            return 50.0
    
    def _extract_required_years(self, job_description: str) -> float:
        """Extract required years of experience from job description"""
        patterns = [
            r'(\d+)\+?\s*years?\s+(?:of\s+)?experience',
            r'minimum\s+of\s+(\d+)\s+years?',
            r'at\s+least\s+(\d+)\s+years?'
        ]
        
        for pattern in patterns:
            matches = re.findall(pattern, job_description.lower())
            if matches:
                try:
                    return float(matches[0])
                except:
                    pass
        
        return None
    
    def _generate_feedback(self, scores: Dict, candidate_info: Dict) -> List[str]:
        """Generate constructive feedback for the candidate"""
        feedback = []
        
        # Skills feedback
        if scores['skills_match'] >= 80:
            feedback.append("✓ Excellent skill match with job requirements")
        elif scores['skills_match'] >= 60:
            feedback.append("• Good skill match, could improve in some areas")
        else:
            feedback.append("⚠ Limited skill match - consider additional training")
        
        # Experience feedback
        if scores['experience'] >= 80:
            feedback.append("✓ Strong experience level for this role")
        elif scores['experience'] >= 60:
            feedback.append("• Adequate experience, on track for this position")
        else:
            feedback.append("⚠ May need more experience for this role")
        
        # Education feedback
        if scores['education'] >= 80:
            feedback.append("✓ Education requirements fully met")
        elif scores['education'] >= 60:
            feedback.append("• Education level is acceptable")
        else:
            feedback.append("⚠ Education may not fully meet requirements")
        
        # Overall strengths
        if candidate_info.get('certifications'):
            feedback.append(f"✓ Has relevant certifications: {', '.join(candidate_info['certifications'][:3])}")
        
        if candidate_info.get('skills') and len(candidate_info['skills']) > 5:
            feedback.append(f"✓ Diverse skill set with {len(candidate_info['skills'])} identified skills")
        
        return feedback
    
    def _get_grade(self, score: float) -> str:
        """Convert numeric score to letter grade"""
        if score >= 90:
            return "A"
        elif score >= 80:
            return "B"
        elif score >= 70:
            return "C"
        elif score >= 60:
            return "D"
        else:
            return "F"
    
    def rank_candidates(self, scored_candidates: List[Dict]) -> List[Dict]:
        """Rank candidates by total score"""
        ranked = sorted(scored_candidates, key=lambda x: x['total_score'], reverse=True)
        
        # Add rank numbers
        for i, candidate in enumerate(ranked, 1):
            candidate['rank'] = i
        
        return ranked
