"""
Candidate Scorer - Score and rank candidates based on job requirements
"""
from typing import Dict, List
import re

class CandidateScorer:
    def __init__(self):
        # Advanced Weighting System - Optimized for Accuracy & Robustness
        self.weights = {
            'skills_match': 0.20,      # Core skills alignment
            'experience': 0.10,        # Years matter less than quality
            'education': 0.05,         # Degree is less critical in modern tech
            'relevance': 0.25,         # CRITICAL: Context & recency of experience
            'technical_depth': 0.15,   # CRITICAL: Seniority/Mastery evidence
            'project_complexity': 0.10, # NEW: Complexity of work done
            'communication': 0.05,     # NEW: Quality of written communication
            'culture_fit': 0.05,       # Soft skills & values alignment
            'keywords': 0.05           # Semantic search backup
        }
        
        # Severity levels for penalties
        self.penalty_config = {
            'missing_critical_skill': 8,    # Per missing must-have
            'max_missing_skills_penalty': 35,
            'low_relevance': 15,            # If relevance < 40
            'very_low_relevance': 25,       # If relevance < 25
            'ai_generated_answers': 12,     # If AI prob > 85%
            'suspected_ai_answers': 5,      # If AI prob > 70%
            'missing_linkedin': 2,
            'red_flag_per_item': 5,         # Per red flag detected
            'max_red_flag_penalty': 20,
            'job_hopping': 10,              # Frequent job changes
            'no_quantifiable_achievements': 8,
            'keyword_stuffing': 12,         # Skills listed but no evidence
        }
        
        # Bonus configurations
        self.bonus_config = {
            'unicorn_candidate': 8,         # High relevance + high depth
            'strong_leadership': 5,         # Leadership score > 80
            'excellent_communication': 3,   # Communication score > 85
            'nice_to_have_skills': 2,       # Per nice-to-have present (max 6)
            'rising_trajectory': 5,         # Career going up
            'top_company_experience': 3,    # Worked at notable companies
        }
    
    def score_candidate(self, candidate_info: Dict, job_description: str, job_title: str, ai_analysis: Dict = None) -> Dict:
        """Score a candidate against job requirements with advanced AI metrics"""
        
        # If AI analysis is not provided, try to generate it on the fly
        if not ai_analysis:
            try:
                from services.ai_service import analyze_candidate_with_ai
                ai_analysis = analyze_candidate_with_ai(
                    candidate_info.get('raw_text', ''), 
                    job_description
                )
            except Exception as e:
                print(f"Auto-AI analysis failed: {e}")

        # Initialize AI-derived metrics with defaults
        ai_data = {}
        if ai_analysis and 'extracted_data' in ai_analysis:
            ai_data = ai_analysis['extracted_data']
            
            # Merge skills from AI
            ai_skills = ai_data.get('skills', [])
            if ai_skills:
                current_skills = set(s.lower() for s in candidate_info.get('skills', []))
                for s in ai_skills:
                    current_skills.add(s.lower())
                candidate_info['skills'] = [s.title() for s in current_skills]
                
            # Update experience/education if missing
            if ai_data.get('years_of_experience') is not None:
                if not candidate_info.get('experience_years'):
                    candidate_info['experience_years'] = float(ai_data['years_of_experience'])
            
            if ai_data.get('education_level') and ai_data['education_level'] != 'Unknown':
                if not candidate_info.get('education'):
                    candidate_info['education'] = [{'degree': ai_data['education_level']}]

        # --- 1. Advanced Skills Scoring ---
        # Base: Keyword Match
        base_skills_score = self._score_skills(candidate_info.get('skills', []), job_description)
        
        # AI Semantic Match (if available)
        ai_skills_score = ai_data.get('skills_match_score')
        if ai_skills_score is not None:
            # Weighted: 80% AI (Semantic), 20% Keyword (Exact) - Trust AI more
            skills_score = (float(ai_skills_score) * 0.8) + (base_skills_score * 0.2)
        else:
            skills_score = base_skills_score

        # --- 2. Experience & Relevance ---
        raw_experience_score = self._score_experience(candidate_info.get('experience_years'), job_description)
        relevance_score = float(ai_data.get('relevance_score', 50)) # Default to neutral if AI fails
        
        # --- 3. Technical Depth ---
        tech_depth_score = float(ai_data.get('technical_depth_score', 50))
        
        # --- 4. Culture Fit ---
        culture_score = float(ai_data.get('culture_fit_score', 50))
        
        # --- 5. NEW: Project Complexity ---
        project_complexity_score = float(ai_data.get('project_complexity_score', 50))
        
        # --- 6. NEW: Communication Quality ---
        communication_score = float(ai_data.get('communication_score', 50))

        # --- 7. Calculate Components ---
        scores = {
            'skills_match': skills_score,
            'experience': raw_experience_score,
            'education': self._score_education(candidate_info.get('education', []), job_description),
            'relevance': relevance_score,
            'technical_depth': tech_depth_score,
            'project_complexity': project_complexity_score,
            'communication': communication_score,
            'culture_fit': culture_score,
            'keywords': self._score_keywords(candidate_info.get('raw_text', ''), job_description)
        }
        
        # --- 8. Weighted Total ---
        total_score = sum(scores[key] * self.weights.get(key, 0) for key in scores)
        
        # --- 9. PENALTIES (Intelligent & Contextual) ---
        penalties_applied = []
        
        # Penalty: Missing Must-Haves (Stricter)
        missing_critical = ai_data.get('missing_must_haves', [])
        if missing_critical:
            penalty = min(len(missing_critical) * self.penalty_config['missing_critical_skill'], 
                         self.penalty_config['max_missing_skills_penalty'])
            total_score -= penalty
            penalties_applied.append(f"-{penalty} pts: Missing critical skills ({', '.join(missing_critical[:3])})")
            print(f"Applied penalty of {penalty} for missing: {missing_critical}")
            
        # Penalty: Low Relevance (Tiered)
        if relevance_score < 25:
            penalty = self.penalty_config['very_low_relevance']
            total_score -= penalty
            penalties_applied.append(f"-{penalty} pts: Very low relevance to job")
            print(f"Applied penalty of {penalty} for very low relevance ({relevance_score})")
        elif relevance_score < 40:
            penalty = self.penalty_config['low_relevance']
            total_score -= penalty
            penalties_applied.append(f"-{penalty} pts: Low relevance to job")
            print(f"Applied penalty of {penalty} for low relevance ({relevance_score})")

        # Penalty: AI Generated Answers (Tiered)
        ai_prob = float(ai_data.get('ai_generated_probability', 0))
        if ai_prob > 85:
            penalty = self.penalty_config['ai_generated_answers']
            total_score -= penalty
            penalties_applied.append(f"-{penalty} pts: Likely AI-generated answers ({int(ai_prob)}%)")
            print(f"Applied penalty of {penalty} for AI answers (Prob: {ai_prob}%)")
        elif ai_prob > 70:
            penalty = self.penalty_config['suspected_ai_answers']
            total_score -= penalty
            penalties_applied.append(f"-{penalty} pts: Suspected AI-generated answers")
            print(f"Applied penalty of {penalty} for suspected AI answers (Prob: {ai_prob}%)")
        
        # Penalty: Missing LinkedIn Profile
        linkedin_url = candidate_info.get('linkedin_url', '')
        if not linkedin_url or not linkedin_url.strip():
            penalty = self.penalty_config['missing_linkedin']
            total_score -= penalty
            penalties_applied.append(f"-{penalty} pts: No LinkedIn profile")
            print(f"Applied penalty of {penalty} for missing LinkedIn profile")
        
        # Penalty: Red Flags (NEW)
        red_flags = ai_analysis.get('red_flags', []) if ai_analysis else []
        if red_flags:
            penalty = min(len(red_flags) * self.penalty_config['red_flag_per_item'],
                         self.penalty_config['max_red_flag_penalty'])
            total_score -= penalty
            penalties_applied.append(f"-{penalty} pts: Red flags detected")
            print(f"Applied penalty of {penalty} for red flags: {red_flags}")
        
        # --- 10. BONUSES (Reward Excellence) ---
        bonuses_applied = []
        
        # Bonus: Unicorn Candidate (High Relevance + High Depth)
        if relevance_score > 85 and tech_depth_score > 85:
            bonus = self.bonus_config['unicorn_candidate']
            total_score += bonus
            bonuses_applied.append(f"+{bonus} pts: Exceptional relevance & depth")
            
        # Bonus: Strong Leadership
        leadership_score = float(ai_data.get('leadership_score', 0))
        if leadership_score > 80:
            bonus = self.bonus_config['strong_leadership']
            total_score += bonus
            bonuses_applied.append(f"+{bonus} pts: Strong leadership evidence")
            
        # Bonus: Excellent Communication
        if communication_score > 85:
            bonus = self.bonus_config['excellent_communication']
            total_score += bonus
            bonuses_applied.append(f"+{bonus} pts: Excellent communication")
            
        # Bonus: Nice-to-Have Skills
        nice_to_haves = ai_data.get('nice_to_haves_present', [])
        if nice_to_haves:
            bonus = min(len(nice_to_haves) * self.bonus_config['nice_to_have_skills'], 6)
            total_score += bonus
            bonuses_applied.append(f"+{bonus} pts: Bonus skills ({len(nice_to_haves)})")
            
        # Bonus: Rising Career Trajectory
        growth = ai_data.get('growth_trajectory', 'Unknown')
        if growth == 'Rising':
            bonus = self.bonus_config['rising_trajectory']
            total_score += bonus
            bonuses_applied.append(f"+{bonus} pts: Rising career trajectory")
            
        # Apply generic AI adjustment (expanded range)
        ai_adjustment = 0
        if ai_analysis and 'score_adjustment' in ai_analysis:
            try:
                ai_adjustment = float(ai_analysis['score_adjustment'])
                ai_adjustment = max(-20, min(20, ai_adjustment))  # Clamp to -20 to +20
                total_score += ai_adjustment
                if ai_adjustment > 0:
                    bonuses_applied.append(f"+{ai_adjustment} pts: AI assessment boost")
                elif ai_adjustment < 0:
                    penalties_applied.append(f"{ai_adjustment} pts: AI assessment adjustment")
            except:
                pass
        
        # Clamp final score
        total_score = max(0.0, min(100.0, total_score))
        
        # Handle parsing failure
        if candidate_info.get('parsing_failed'):
            feedback = ["⚠ Resume parsing failed - Manual review required"]
        else:
            feedback = self._generate_feedback(scores, candidate_info)
            # Add critical warnings at the top
            if red_flags:
                feedback.insert(0, f"🚩 Red Flags: {', '.join(red_flags[:3])}")
            if missing_critical:
                feedback.insert(0, f"⚠ Missing Critical Skills: {', '.join(missing_critical[:3])}")
            if ai_prob > 70:
                feedback.append(f"⚠ Possible AI-generated answers ({int(ai_prob)}%)")
            # Add bonuses/penalties summary
            if bonuses_applied:
                feedback.append(f"✅ Bonuses: {'; '.join(bonuses_applied[:3])}")
            if penalties_applied:
                feedback.append(f"❌ Penalties: {'; '.join(penalties_applied[:3])}")
        
        # Get AI recommendation
        ai_recommendation = ai_data.get('overall_recommendation', self._get_grade(total_score))
        
        result = {
            'total_score': round(total_score, 2),
            'breakdown': {k: round(v, 2) for k, v in scores.items()},
            'feedback': feedback,
            'grade': self._get_grade(total_score),
            'candidate_name': candidate_info.get('name') or candidate_info.get('candidate_name') or 'Unknown',
            'candidate_email': candidate_info.get('email') or candidate_info.get('candidate_email') or 'N/A',
            'candidate_phone': candidate_info.get('phone') or candidate_info.get('candidate_phone') or 'N/A',
            'linkedin_url': candidate_info.get('linkedin_url', ''),
            'file_url': candidate_info.get('file_url', ''),
            'parsing_failed': candidate_info.get('parsing_failed', False),
            'status': candidate_info.get('status', 'applied'), # Default to 'applied' for Kanban
            'ai_analysis': ai_analysis # Include full AI analysis for frontend
        }
        
        # Preserve ID if it exists
        if 'id' in candidate_info:
            result['id'] = candidate_info['id']
        
        # Add AI insights if available
        if ai_analysis:
            result['ai_analysis'] = {
                'pros': ai_analysis.get('pros', []),
                'cons': ai_analysis.get('cons', []),
                'summary': ai_analysis.get('summary', ''),
                'adjustment': ai_adjustment,
                'red_flags': red_flags,
                'recommendation': ai_recommendation,
                'penalties': penalties_applied,
                'bonuses': bonuses_applied
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
        # Reward breadth of relevant skills.
        # We assume finding ~10 relevant skills is a "good" match (100%).
        # Previously was 5 skills (multiplier 20), now 10 skills (multiplier 10).
        
        count_score = min(len(matched_skills) * 10.0, 100.0) 
        
        # Density Bonus: Reward candidates whose skills are MOSTLY relevant
        # (Avoids "keyword stuffing" where they list 100 skills and 5 match)
        if len(candidate_skills) > 0:
            density = len(matched_skills) / len(candidate_skills)
            if density > 0.5:
                count_score = min(count_score + 5, 100) # +5% bonus for high relevance density
        
        return count_score
    
    def _score_experience(self, years: float, job_description: str) -> float:
        """Score based on experience (0-100) with bonuses/penalties"""
        if years is None:
            return 50.0  # Neutral score if not specified
        
        # Extract required years from job description
        required_years = self._extract_required_years(job_description)
        
        if required_years is None:
            # No specific requirement, score based on general experience
            # Adjusted scale: Senior is 7+, Mid is 4+
            if years < 1:
                return 30.0
            elif years < 2:
                return 50.0
            elif years < 4:
                return 70.0
            elif years < 7:
                return 85.0
            else:
                return 100.0
        
        # Score based on how close to required
        if years >= required_years:
            # Bonus for exceeding requirements significantly
            if years >= required_years + 3:
                return 100.0 # Cap at 100, but ensures max score
            elif years >= required_years + 1:
                return 100.0
            return 95.0 # Met exact requirement
            
        elif years >= required_years * 0.75:
            return 75.0 # Close enough
        elif years >= required_years * 0.5:
            return 50.0 # Halfway there - significant penalty
        else:
            return 20.0 # Not close - heavy penalty
    
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
