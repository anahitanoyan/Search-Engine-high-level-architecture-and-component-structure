import hashlib
import mmh3
from collections import defaultdict
import redis
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class DuplicateDetector:
    def __init__(self):
        self.redis_client = redis.from_url(Config.REDIS_URL)
        self.url_hashes = set()
        self.content_hashes = set()
        self.similarity_threshold = 0.85
        
    def is_duplicate_url(self, url):
        """Check if URL is duplicate"""
        url_normalized = self.normalize_url(url)
        url_hash = self.hash_string(url_normalized)
        
        # Check in Redis first
        if self.redis_client.sismember('seen_urls', url_hash):
            return True
            
        # Check in local cache
        if url_hash in self.url_hashes:
            return True
            
        # Add to both caches
        self.url_hashes.add(url_hash)
        self.redis_client.sadd('seen_urls', url_hash)
        return False
        
    def is_duplicate_content(self, content, url):
        """Check if content is duplicate using fingerprinting"""
        # Create content fingerprint
        fingerprint = self.create_content_fingerprint(content)
        
        # Check against existing fingerprints
        for existing_fingerprint in self.content_hashes:
            similarity = self.calculate_similarity(fingerprint, existing_fingerprint)
            if similarity > self.similarity_threshold:
                logger.info(f"Duplicate content detected for {url}")
                return True
                
        # Store new fingerprint
        self.content_hashes.add(fingerprint)
        self.redis_client.sadd('content_fingerprints', str(fingerprint))
        return False
        
    def normalize_url(self, url):
        """Normalize URL for duplicate detection"""
        from urllib.parse import urlparse, urlunparse
        
        parsed = urlparse(url.lower())
        
        # Remove common parameters that don't affect content
        if parsed.query:
            # Remove tracking parameters
            tracking_params = ['utm_source', 'utm_medium', 'utm_campaign', 
                             'utm_term', 'utm_content', 'ref', 'source']
            query_parts = []
            for param in parsed.query.split('&'):
                if '=' in param:
                    key, value = param.split('=', 1)
                    if key not in tracking_params:
                        query_parts.append(param)
            normalized_query = '&'.join(sorted(query_parts))
        else:
            normalized_query = ''
            
        # Remove fragment
        normalized = urlunparse((
            parsed.scheme,
            parsed.netloc,
            parsed.path.rstrip('/'),
            parsed.params,
            normalized_query,
            ''  # Remove fragment
        ))
        
        return normalized
        
    def create_content_fingerprint(self, content):
        """Create content fingerprint using shingling"""
        # Remove HTML tags and normalize text
        from bs4 import BeautifulSoup
        import re
        
        soup = BeautifulSoup(content, 'html.parser')
        text = soup.get_text()
        text = re.sub(r'\s+', ' ', text).lower().strip()
        
        # Create 5-gram shingles
        shingles = set()
        words = text.split()
        
        for i in range(len(words) - 4):
            shingle = ' '.join(words[i:i+5])
            shingle_hash = mmh3.hash(shingle)
            shingles.add(shingle_hash)
            
        return frozenset(shingles)
        
    def calculate_similarity(self, fingerprint1, fingerprint2):
        """Calculate Jaccard similarity between fingerprints"""
        if not fingerprint1 or not fingerprint2:
            return 0.0
            
        intersection = len(fingerprint1.intersection(fingerprint2))
        union = len(fingerprint1.union(fingerprint2))
        
        return intersection / union if union > 0 else 0.0
        
    def hash_string(self, text):
        """Create hash of string"""
        return hashlib.sha256(text.encode('utf-8')).hexdigest()
        
    def clear_cache(self):
        """Clear duplicate detection cache"""
        self.url_hashes.clear()
        self.content_hashes.clear()
        self.redis_client.delete('seen_urls', 'content_fingerprints')
