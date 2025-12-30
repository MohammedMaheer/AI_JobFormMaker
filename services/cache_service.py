"""
Cache Service - Uses Upstash Redis (free tier) for serverless caching
Setup: 
1. Go to https://upstash.com/ and create a free account
2. Create a new Redis database (free tier = 10,000 commands/day)
3. Copy UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN to your .env file
"""

import os
import json
import hashlib
from datetime import datetime
from functools import wraps

# Try to import upstash-redis, fall back to in-memory cache if not available
try:
    from upstash_redis import Redis
    UPSTASH_AVAILABLE = True
except ImportError:
    UPSTASH_AVAILABLE = False
    print("upstash-redis not installed. Using in-memory cache fallback.")


class CacheService:
    """
    Hybrid cache service that uses:
    - Upstash Redis when available (production/Vercel)
    - In-memory dict fallback for local development
    """
    
    # Default TTL values (in seconds)
    TTL_SHORT = 60           # 1 minute - for frequently changing data
    TTL_MEDIUM = 300         # 5 minutes - for job listings, counts
    TTL_LONG = 3600          # 1 hour - for analytics, aggregates
    TTL_PERMANENT = 86400    # 24 hours - for AI scores, processed data
    
    def __init__(self):
        self.redis = None
        self.memory_cache = {}  # Fallback in-memory cache
        self.memory_timestamps = {}  # Track expiry for memory cache
        
        # Initialize Upstash Redis if credentials are available
        redis_url = os.getenv('UPSTASH_REDIS_REST_URL')
        redis_token = os.getenv('UPSTASH_REDIS_REST_TOKEN')
        
        if UPSTASH_AVAILABLE and redis_url and redis_token:
            try:
                self.redis = Redis(url=redis_url, token=redis_token)
                # Test connection
                self.redis.ping()
                print("✅ Upstash Redis connected successfully")
            except Exception as e:
                print(f"⚠️ Failed to connect to Upstash Redis: {e}")
                self.redis = None
        else:
            if not UPSTASH_AVAILABLE:
                print("ℹ️ Using in-memory cache (install upstash-redis for Redis support)")
            else:
                print("ℹ️ Using in-memory cache (set UPSTASH_REDIS_REST_URL and UPSTASH_REDIS_REST_TOKEN for Redis)")
    
    @property
    def is_redis(self):
        """Check if using Redis or memory cache"""
        return self.redis is not None
    
    def _generate_key(self, prefix: str, *args) -> str:
        """Generate a cache key from prefix and arguments"""
        key_parts = [prefix] + [str(arg) for arg in args if arg is not None]
        return ":".join(key_parts)
    
    def get(self, key: str):
        """Get value from cache"""
        try:
            if self.redis:
                value = self.redis.get(key)
                if value:
                    return json.loads(value) if isinstance(value, str) else value
            else:
                # Memory cache with TTL check
                if key in self.memory_cache:
                    expiry = self.memory_timestamps.get(key, 0)
                    if expiry == 0 or datetime.now().timestamp() < expiry:
                        return self.memory_cache[key]
                    else:
                        # Expired
                        del self.memory_cache[key]
                        del self.memory_timestamps[key]
        except Exception as e:
            print(f"Cache get error: {e}")
        return None
    
    def set(self, key: str, value, ttl: int = None):
        """Set value in cache with optional TTL"""
        try:
            if self.redis:
                json_value = json.dumps(value) if not isinstance(value, str) else value
                if ttl:
                    self.redis.setex(key, ttl, json_value)
                else:
                    self.redis.set(key, json_value)
            else:
                # Memory cache
                self.memory_cache[key] = value
                if ttl:
                    self.memory_timestamps[key] = datetime.now().timestamp() + ttl
                else:
                    self.memory_timestamps[key] = 0  # No expiry
            return True
        except Exception as e:
            print(f"Cache set error: {e}")
            return False
    
    def delete(self, key: str):
        """Delete a key from cache"""
        try:
            if self.redis:
                self.redis.delete(key)
            else:
                self.memory_cache.pop(key, None)
                self.memory_timestamps.pop(key, None)
            return True
        except Exception as e:
            print(f"Cache delete error: {e}")
            return False
    
    def delete_pattern(self, pattern: str):
        """Delete all keys matching a pattern (e.g., 'jobs:*')"""
        try:
            if self.redis:
                # Upstash REST API doesn't support SCAN, so we track keys manually
                # For now, we'll just delete known keys
                pass
            else:
                # Memory cache - find and delete matching keys
                keys_to_delete = [k for k in self.memory_cache.keys() if k.startswith(pattern.replace('*', ''))]
                for key in keys_to_delete:
                    del self.memory_cache[key]
                    self.memory_timestamps.pop(key, None)
            return True
        except Exception as e:
            print(f"Cache delete pattern error: {e}")
            return False
    
    def invalidate_jobs(self):
        """Invalidate all job-related cache"""
        self.delete('jobs:all')
        self.delete('dashboard:stats')
    
    def invalidate_candidates(self, job_id: str = None):
        """Invalidate candidate-related cache"""
        if job_id:
            self.delete(f'candidates:job:{job_id}')
            self.delete(f'candidates:count:{job_id}')
        self.delete('dashboard:stats')
        self.delete('analytics:data')
    
    # ==========================================
    # Convenience methods for common operations
    # ==========================================
    
    def get_jobs(self):
        """Get cached job list"""
        return self.get('jobs:all')
    
    def set_jobs(self, jobs):
        """Cache job list"""
        return self.set('jobs:all', jobs, self.TTL_MEDIUM)
    
    def get_job(self, job_id: str):
        """Get cached single job"""
        return self.get(f'job:{job_id}')
    
    def set_job(self, job_id: str, job):
        """Cache single job"""
        return self.set(f'job:{job_id}', job, self.TTL_MEDIUM)
    
    def get_candidates(self, job_id: str):
        """Get cached candidates for a job"""
        return self.get(f'candidates:job:{job_id}')
    
    def set_candidates(self, job_id: str, candidates):
        """Cache candidates for a job"""
        return self.set(f'candidates:job:{job_id}', candidates, self.TTL_SHORT)
    
    def get_dashboard_stats(self):
        """Get cached dashboard statistics"""
        return self.get('dashboard:stats')
    
    def set_dashboard_stats(self, stats):
        """Cache dashboard statistics"""
        return self.set('dashboard:stats', stats, self.TTL_SHORT)
    
    def get_analytics(self):
        """Get cached analytics data"""
        return self.get('analytics:data')
    
    def set_analytics(self, data):
        """Cache analytics data"""
        return self.set('analytics:data', data, self.TTL_MEDIUM)
    
    def get_ai_score(self, candidate_id: str):
        """Get cached AI score for a candidate"""
        return self.get(f'ai:score:{candidate_id}')
    
    def set_ai_score(self, candidate_id: str, score_data):
        """Cache AI score for a candidate (long TTL since it doesn't change)"""
        return self.set(f'ai:score:{candidate_id}', score_data, self.TTL_PERMANENT)


# Decorator for caching function results
def cached(key_prefix: str, ttl: int = CacheService.TTL_MEDIUM):
    """
    Decorator to cache function results
    
    Usage:
        @cached('analytics', ttl=300)
        def get_analytics_data():
            # expensive computation
            return data
    """
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            # Import here to avoid circular imports
            from app import cache_service
            
            # Generate cache key from function name and args
            cache_key = f"{key_prefix}:{func.__name__}"
            if args:
                args_hash = hashlib.md5(str(args).encode()).hexdigest()[:8]
                cache_key += f":{args_hash}"
            
            # Try to get from cache
            cached_result = cache_service.get(cache_key)
            if cached_result is not None:
                return cached_result
            
            # Execute function and cache result
            result = func(*args, **kwargs)
            cache_service.set(cache_key, result, ttl)
            return result
        return wrapper
    return decorator


# Create singleton instance
cache_service = CacheService()
