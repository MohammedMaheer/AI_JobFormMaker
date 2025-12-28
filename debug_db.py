from services.storage_service import StorageService
import json

try:
    storage = StorageService()
    candidates = storage.get_all_candidates()
    print(f"Found {len(candidates)} candidates in database.")
    for c in candidates:
        print(f"ID: {c.get('id')}")
        print(f"  Name: {c.get('name')}")
        print(f"  Total Score: {c.get('total_score')}")
        print(f"  Breakdown: {c.get('breakdown')}")
        print(f"  AI Analysis Keys: {list(c.get('ai_analysis', {}).keys()) if c.get('ai_analysis') else 'None'}")
        if c.get('ai_analysis'):
             print(f"  AI Summary: {c['ai_analysis'].get('summary')[:50]}...")
        
        # Check raw_data as well
        raw = c.get('raw_data', {})
        print(f"  Raw Breakdown: {raw.get('breakdown')}")
        print(f"  Raw AI Analysis Keys: {list(raw.get('ai_analysis', {}).keys()) if raw.get('ai_analysis') else 'None'}")

except Exception as e:
    print(f"Error: {e}")
