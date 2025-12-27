import json
import os
from datetime import datetime
from typing import List, Dict, Optional

DATA_DIR = 'data'
CANDIDATES_FILE = os.path.join(DATA_DIR, 'candidates.json')

class StorageService:
    def __init__(self):
        self._ensure_data_dir()
    
    def _ensure_data_dir(self):
        if not os.path.exists(DATA_DIR):
            os.makedirs(DATA_DIR)
        if not os.path.exists(CANDIDATES_FILE):
            with open(CANDIDATES_FILE, 'w') as f:
                json.dump([], f)
    
    def get_all_candidates(self) -> List[Dict]:
        try:
            with open(CANDIDATES_FILE, 'r') as f:
                return json.load(f)
        except Exception as e:
            print(f"Error reading candidates: {e}")
            return []
    
    def save_candidate(self, candidate_data: Dict) -> Dict:
        candidates = self.get_all_candidates()
        
        # Add ID and timestamp if missing
        if 'id' not in candidate_data:
            candidate_data['id'] = f"cand_{int(datetime.now().timestamp())}_{len(candidates)}"
        if 'timestamp' not in candidate_data:
            candidate_data['timestamp'] = datetime.now().isoformat()
            
        # Check if candidate already exists (by email or id)
        existing_index = -1
        for i, c in enumerate(candidates):
            if c.get('id') == candidate_data.get('id'):
                existing_index = i
                break
            # Optional: Update by email if ID not provided? 
            # For now, let's stick to ID or append new.
            
        if existing_index >= 0:
            candidates[existing_index] = candidate_data
        else:
            candidates.append(candidate_data)
            
        self._save_to_file(candidates)
        return candidate_data
    
    def _save_to_file(self, data: List[Dict]):
        with open(CANDIDATES_FILE, 'w') as f:
            json.dump(data, f, indent=2)

    def clear_candidates(self):
        self._save_to_file([])
