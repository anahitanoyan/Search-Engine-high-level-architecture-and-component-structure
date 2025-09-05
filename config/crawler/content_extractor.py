from bs4 import BeautifulSoup
import re
from urllib.parse import urlparse

class ContentExtractor:
    def __init__(self):
        self.text_tags = ['p', 'div', 'span', 'article', 'section']
        self.heading_tags = ['h1', 'h2', 'h3', 'h4', 'h5', 'h6']
        
    def extract(self, html_content, url):
        """Extract structured content from HTML"""
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Remove script and style elements
        for script in soup(["script", "style", "nav", "footer"]):
            script.decompose()
            
        return {
            'title': self.extract_title(soup),
            'meta_description': self.extract_meta_description(soup),
            'headings': self.extract_headings(soup),
            'body_text': self.extract_body_text(soup),
            'links_text': self.extract_links_text(soup),
            'images': self.extract_images(soup, url),
            'word_count': self.count_words(soup.get_text()),
            'language': self.detect_language(soup)
        }
        
    def extract_title(self, soup):
        """Extract page title"""
        title_tag = soup.find('title')
        if title_tag:
            return title_tag.get_text().strip()
            
        # Fallback to h1
        h1_tag = soup.find('h1')
        if h1_tag:
            return h1_tag.get_text().strip()
            
        return ""
        
    def extract_meta_description(self, soup):
        """Extract meta description"""
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            return meta_desc['content'].strip()
        return ""
        
    def extract_headings(self, soup):
        """Extract all headings with hierarchy"""
        headings = []
        for tag in self.heading_tags:
            for heading in soup.find_all(tag):
                headings.append({
                    'level': int(tag[1]),
                    'text': heading.get_text().strip()
                })
        return headings
        
    def extract_body_text(self, soup):
        """Extract main body text"""
        # Remove non-content elements
        for element in soup(['nav', 'footer', 'sidebar', 'aside']):
            element.decompose()
            
        # Get text from main content areas
        main_content = soup.find('main') or soup.find('article') or soup.find('body')
        if main_content:
            text = main_content.get_text()
        else:
            text = soup.get_text()
            
        # Clean up text
        text = re.sub(r'\s+', ' ', text)
        return text.strip()
        
    def extract_links_text(self, soup):
        """Extract anchor text from links"""
        links_text = []
        for link in soup.find_all('a', href=True):
            text = link.get_text().strip()
            if text:
                links_text.append(text)
        return ' '.join(links_text)
        
    def extract_images(self, soup, base_url):
        """Extract image information"""
        images = []
        for img in soup.find_all('img'):
            src = img.get('src')
            if src:
                images.append({
                    'src': src,
                    'alt': img.get('alt', ''),
                    'title': img.get('title', '')
                })
        return images
        
    def count_words(self, text):
        """Count words in text"""
        words = re.findall(r'\b\w+\b', text.lower())
        return len(words)
        
    def detect_language(self, soup):
        """Detect page language"""
        html_tag = soup.find('html')
        if html_tag and html_tag.get('lang'):
            return html_tag['lang']
        return 'en'  # Default to English
