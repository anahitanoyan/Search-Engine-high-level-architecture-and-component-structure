import asyncio
import logging
from crawler.web_crawler import WebCrawler
from indexer.inverted_index import InvertedIndex
from ranker.tf_idf import TFIDFScorer

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

async def main():
    """Main function to run the search engine"""
    logger.info("Starting search engine...")
    
    # Initialize components
    crawler = WebCrawler(max_concurrent=5)
    inverted_index = InvertedIndex()
    
    # Seed URLs for crawling
    seed_urls = [
        'https://example.com',
        'https://en.wikipedia.org/wiki/Main_Page',
        'https://news.ycombinator.com'
    ]
    
    logger.info(f"Starting crawl with {len(seed_urls)} seed URLs")
    
    # Start crawling
    await crawler.crawl(seed_urls)
    
    logger.info("Crawling completed!")
    logger.info(f"Index stats: {inverted_index.get_stats()}")

if __name__ == "__main__":
    asyncio.run(main())
