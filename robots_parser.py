import urllib.robotparser
from urllib.parse import urljoin, urlparse
import asyncio
import aiohttp
from config.settings import Config
import logging

logger = logging.getLogger(__name__)

class RobotsParser:
    def __init__(self):
        self.robots_cache = {}
        self.cache_expiry = 3600  # 1 hour cache
        
    async def can_fetch(self, url, user_agent=None):
        """Check if URL can be fetched according to robots.txt"""
        if user_agent is None:
            user_agent = Config.USER_AGENT
            
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        # Check cache first
        if robots_url in self.robots_cache:
            rp = self.robots_cache[robots_url]
        else:
            rp = await self._fetch_robots_txt(robots_url)
            self.robots_cache[robots_url] = rp
            
        if rp is None:
            # If robots.txt not found, allow crawling
            return True
            
        return rp.can_fetch(user_agent, url)
        
    async def _fetch_robots_txt(self, robots_url):
        """Fetch and parse robots.txt"""
        try:
            async with aiohttp.ClientSession() as session:
                async with session.get(robots_url, timeout=10) as response:
                    if response.status == 200:
                        content = await response.text()
                        rp = urllib.robotparser.RobotFileParser()
                        rp.set_url(robots_url)
                        rp.read()
                        return rp
                    else:
                        logger.info(f"robots.txt not found: {robots_url}")
                        return None
        except Exception as e:
            logger.error(f"Error fetching robots.txt from {robots_url}: {e}")
            return None
            
    def get_crawl_delay(self, url, user_agent=None):
        """Get crawl delay from robots.txt"""
        if user_agent is None:
            user_agent = Config.USER_AGENT
            
        parsed_url = urlparse(url)
        robots_url = f"{parsed_url.scheme}://{parsed_url.netloc}/robots.txt"
        
        if robots_url in self.robots_cache:
            rp = self.robots_cache[robots_url]
            if rp:
                delay = rp.crawl_delay(user_agent)
                return delay if delay else Config.CRAWL_DELAY
                
        return Config.CRAWL_DELAY
