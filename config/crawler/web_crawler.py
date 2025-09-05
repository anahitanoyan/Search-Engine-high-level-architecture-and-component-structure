import asyncio
import aiohttp
import time
from bs4 import BeautifulSoup
from urllib.parse import urljoin, urlparse
import logging
from .url_frontier import URLFrontier
from .content_extractor import ContentExtractor
from .robots_parser import RobotsParser
from config.settings import Config

logger = logging.getLogger(__name__)

class WebCrawler:
    def __init__(self, max_concurrent=10):
        self.url_frontier = URLFrontier()
        self.content_extractor = ContentExtractor()
        self.robots_parser = RobotsParser()
        self.max_concurrent = max_concurrent
        self.crawled_count = 0
        
    async def crawl(self, seed_urls):
        """Main crawling loop"""
        # Add seed URLs to frontier
        for url in seed_urls:
            self.url_frontier.add_url(url, priority=1)
            
        # Create semaphore for concurrency control
        semaphore = asyncio.Semaphore(self.max_concurrent)
        
        async with aiohttp.ClientSession(
            timeout=aiohttp.ClientTimeout(total=Config.REQUEST_TIMEOUT),
            headers={'User-Agent': Config.USER_AGENT}
        ) as session:
            
            tasks = []
            while not self.url_frontier.is_empty() or tasks:
                # Start new tasks if we have capacity
                while len(tasks) < self.max_concurrent and not self.url_frontier.is_empty():
                    url = self.url_frontier.get_next_url()
                    if url:
                        task = asyncio.create_task(
                            self.crawl_page(session, semaphore, url)
                        )
                        tasks.append(task)
                
                # Wait for at least one task to complete
                if tasks:
                    done, pending = await asyncio.wait(
                        tasks, return_when=asyncio.FIRST_COMPLETED
                    )
                    tasks = list(pending)
                    
                    # Process completed tasks
                    for task in done:
                        try:
                            result = await task
                            if result:
                                await self.process_crawl_result(result)
                        except Exception as e:
                            logger.error(f"Task failed: {e}")
                            
    async def crawl_page(self, session, semaphore, url):
        """Crawl a single page"""
        async with semaphore:
            try:
                # Check robots.txt
                if not await self.robots_parser.can_fetch(url):
                    logger.info(f"Robots.txt disallows crawling: {url}")
                    return None
                    
                # Fetch page
                async with session.get(url) as response:
                    if response.status != 200:
                        logger.warning(f"HTTP {response.status} for {url}")
                        return None
                        
                    content = await response.text()
                    
                    # Extract content and metadata
                    extracted_data = self.content_extractor.extract(content, url)
                    
                    # Extract links for further crawling
                    links = self.extract_links(content, url)
                    
                    self.crawled_count += 1
                    logger.info(f"Crawled {self.crawled_count}: {url}")
                    
                    return {
                        'url': url,
                        'content': extracted_data,
                        'links': links,
                        'status': response.status,
                        'timestamp': time.time()
                    }
                    
            except Exception as e:
                logger.error(f"Error crawling {url}: {e}")
                return None
                
    def extract_links(self, html_content, base_url):
        """Extract links from HTML content"""
        soup = BeautifulSoup(html_content, 'html.parser')
        links = []
        
        for link in soup.find_all('a', href=True):
            href = link['href']
            absolute_url = urljoin(base_url, href)
            
            # Filter out non-HTTP links
            parsed = urlparse(absolute_url)
            if parsed.scheme in ('http', 'https'):
                links.append({
                    'url': absolute_url,
                    'anchor_text': link.get_text().strip(),
                    'title': link.get('title', '')
                })
                
        return links
        
    async def process_crawl_result(self, result):
        """Process crawled page result"""
        # Add new URLs to frontier
        for link in result['links']:
            self.url_frontier.add_url(link['url'], priority=2)
            
        # Here you would typically:
        # 1. Store the document in database
        # 2. Queue for indexing
        # 3. Update link graph for PageRank
        
        # For now, just log
        logger.info(f"Processed page: {result['url']}")
