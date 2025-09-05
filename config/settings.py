import os
from datetime import timedelta

class Config:
    # Crawler settings
    CRAWL_DELAY = float(os.getenv('CRAWL_DELAY', '1.0'))
    MAX_PAGES_PER_DOMAIN = int(os.getenv('MAX_PAGES_PER_DOMAIN', '10000'))
    USER_AGENT = "CustomSearchBot/1.0"
    MAX_CRAWL_THREADS = int(os.getenv('MAX_CRAWL_THREADS', '10'))
    REQUEST_TIMEOUT = 30
    
    # Index settings
    INDEX_BATCH_SIZE = 1000
    MAX_TERM_LENGTH = 100
    MIN_TERM_LENGTH = 2
    
    # Search settings
    MAX_RESULTS_PER_PAGE = 10
    QUERY_TIMEOUT = 5.0
    DEFAULT_RESULTS_COUNT = 20
    
    # Storage
    DATABASE_URL = os.getenv('DATABASE_URL', 'postgresql://user:pass@localhost/searchdb')
    REDIS_URL = os.getenv('REDIS_URL', 'redis://localhost:6379')
    ELASTICSEARCH_URL = os.getenv('ELASTICSEARCH_URL', 'http://localhost:9200')
    
    # Ranking weights
    CONTENT_RELEVANCE_WEIGHT = 0.4
    PAGERANK_WEIGHT = 0.25
    FRESHNESS_WEIGHT = 0.15
    USER_SIGNALS_WEIGHT = 0.1
    TECHNICAL_SEO_WEIGHT = 0.1
    
    # Crawl scheduling
    HIGH_PRIORITY_INTERVAL = timedelta(hours=1)
    MEDIUM_PRIORITY_INTERVAL = timedelta(days=1)
    LOW_PRIORITY_INTERVAL = timedelta(weeks=1)
    
    # Content lifecycle
    DELETION_GRACE_PERIOD = timedelta(weeks=2)
    RECRAWL_ATTEMPTS = 3
