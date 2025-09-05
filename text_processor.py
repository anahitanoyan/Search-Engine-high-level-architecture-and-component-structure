import re
import string
from collections import defaultdict
import nltk
from nltk.corpus import stopwords
from nltk.stem import PorterStemmer
from nltk.tokenize import word_tokenize
import logging

# Download required NLTK data
try:
    nltk.data.find('tokenizers/punkt')
except LookupError:
    nltk.download('punkt')

try:
    nltk.data.find('corpora/stopwords')
except LookupError:
    nltk.download('stopwords')

logger = logging.getLogger(__name__)

class TextProcessor:
    def __init__(self, language='english'):
        self.language = language
        self.stemmer = PorterStemmer()
        self.stop_words = set(stopwords.words(language))
        
        # Add custom stop words
        self.stop_words.update(['would', 'could', 'should', 'might', 'must'])
        
        # Compile regex patterns
        self.url_pattern = re.compile(r'http[s]?://(?:[a-zA-Z]|[0-9]|[$-_@.&+]|[!*\\(\\),]|(?:%[0-9a-fA-F][0-9a-fA-F]))+')
        self.email_pattern = re.compile(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b')
        self.number_pattern = re.compile(r'\b\d+\b')
        
    def process_text(self, text):
        """Main text processing pipeline"""
        # Clean and normalize text
        cleaned_text = self.clean_text(text)
        
        # Tokenize
        tokens = self.tokenize(cleaned_text)
        
        # Filter and normalize tokens
        processed_tokens = []
        for token in tokens:
            processed_token = self.process_token(token)
            if processed_token:
                processed_tokens.append(processed_token)
                
        return processed_tokens
        
    def clean_text(self, text):
        """Clean and normalize text"""
        # Convert to lowercase
        text = text.lower()
        
        # Remove URLs
        text = self.url_pattern.sub(' ', text)
        
        # Remove email addresses
        text = self.email_pattern.sub(' ', text)
        
        # Remove numbers (optional)
        # text = self.number_pattern.sub(' ', text)
        
        # Remove extra whitespace
        text = re.sub(r'\s+', ' ', text)
        
        return text.strip()
        
    def tokenize(self, text):
        """Tokenize text into words"""
        try:
            tokens = word_tokenize(text, language=self.language)
        except:
            # Fallback to simple split if NLTK fails
            tokens = text.split()
            
        return tokens
        
    def process_token(self, token):
        """Process individual token"""
        # Remove punctuation
        token = token.translate(str.maketrans('', '', string.punctuation))
        
        # Skip if empty or too short
        if not token or len(token) < 2:
            return None
            
        # Skip if all digits
        if token.isdigit():
            return None
            
        # Skip stop words
        if token in self.stop_words:
            return None
            
        # Stem the token
        try:
            stemmed_token = self.stemmer.stem(token)
            return stemmed_token
        except:
            return token
            
    def extract_features(self, html_content):
        """Extract structured features from HTML content"""
        from bs4 import BeautifulSoup
        
        soup = BeautifulSoup(html_content, 'html.parser')
        
        # Extract different text components with weights
        features = {
            'title': self.extract_title_text(soup),
            'headings': self.extract_heading_text(soup),
            'body': self.extract_body_text(soup),
            'links': self.extract_link_text(soup),
            'meta': self.extract_meta_text(soup)
        }
        
        # Process each feature
        processed_features = {}
        for feature_name, text in features.items():
            if text:
                processed_features[feature_name] = self.process_text(text)
            else:
                processed_features[feature_name] = []
                
        return processed_features
        
    def extract_title_text(self, soup):
        """Extract title text"""
        title_tag = soup.find('title')
        return title_tag.get_text() if title_tag else ''
        
    def extract_heading_text(self, soup):
        """Extract heading text"""
        headings = soup.find_all(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
        return ' '.join([h.get_text() for h in headings])
        
    def extract_body_text(self, soup):
        """Extract body text"""
        # Remove script and style elements
        for script in soup(['script', 'style', 'nav', 'footer']):
            script.decompose()
            
        return soup.get_text()
        
    def extract_link_text(self, soup):
        """Extract anchor text"""
        links = soup.find_all('a')
        return ' '.join([link.get_text() for link in links])
        
    def extract_meta_text(self, soup):
        """Extract meta description and keywords"""
        meta_texts = []
        
        # Meta description
        meta_desc = soup.find('meta', attrs={'name': 'description'})
        if meta_desc and meta_desc.get('content'):
            meta_texts.append(meta_desc['content'])
            
        # Meta keywords
        meta_keywords = soup.find('meta', attrs={'name': 'keywords'})
        if meta_keywords and meta_keywords.get('content'):
            meta_texts.append(meta_keywords['content'])
            
        return ' '.join(meta_texts)
        
    def calculate_term_weights(self, processed_features):
        """Calculate weighted terms based on HTML structure"""
        term_weights = defaultdict(float)
        
        # Weight different HTML elements
        weights = {
            'title': 3.0,
            'headings': 2.0,
            'body': 1.0,
            'links': 0.8,
            'meta': 1.5
        }
        
        for feature_name, terms in processed_features.items():
            weight = weights.get(feature_name, 1.0)
            for term in terms:
                term_weights[term] += weight
                
        return dict(term_weights)
