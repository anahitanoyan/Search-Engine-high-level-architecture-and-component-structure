import heapq
import time
from collections import defaultdict, deque
from urllib.parse import urlparse
import redis
from config.settings import Config

class URLFrontier:
    def __init__(self):
        self.priority_queue = []
        self.domain_queues = defaultdict(deque)
        self.domain_last_access = defaultdict(float)
        self.crawled_urls = set()
        self.robots_cache = {}
        self.redis_client = redis.from_url(Config.REDIS_URL)
        
    def add_url(self, url, priority=1):
        """Add URL to frontier with priority"""
        if url in self.crawled_urls:
            return False
            
        domain = urlparse(url).netloc
        
        # Add to priority queue and domain-specific queue
        heapq.heappush(self.priority_queue, (priority, time.time(), url))
        self.domain_queues[domain].append(url)
        
        # Store in Redis for persistence
        self.redis_client.sadd('frontier_urls', url)
        return True
        
    def get_next_url(self):
        """Get next URL respecting politeness policies"""
        current_time = time.time()
        
        while self.priority_queue:
            priority, timestamp, url = heapq.heappop(self.priority_queue)
            domain = urlparse(url).netloc
            
            # Check if we need to wait for this domain
            last_access = self.domain_last_access.get(domain, 0)
            if current_time - last_access < Config.CRAWL_DELAY:
                # Re-add to queue with updated timestamp
                heapq.heappush(self.priority_queue, 
                             (priority, current_time + Config.CRAWL_DELAY, url))
                continue
                
            # Update last access time
            self.domain_last_access[domain] = current_time
            self.crawled_urls.add(url)
            
            # Remove from Redis
            self.redis_client.srem('frontier_urls', url)
            return url
            
        return None
        
    def is_empty(self):
        return len(self.priority_queue) == 0
        
    def size(self):
        return len(self.priority_queue)
