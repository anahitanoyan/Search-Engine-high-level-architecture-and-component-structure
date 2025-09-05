import re
from typing import List, Dict, Tuple
from collections import defaultdict
import string
from indexer.text_processor import TextProcessor

class QueryParser:
    def __init__(self):
        self.text_processor = TextProcessor()
        self.query_operators = {
            'AND': '&',
            'OR': '|',
            'NOT': '-'
        }
        
    def parse_query(self, raw_query):
        """Parse and process search query"""
        # Detect query type and intent
        query_type = self._detect_query_type(raw_query)
        intent = self._detect_intent(raw_query)
        
        # Handle quoted phrases
        phrases, remaining_query = self._extract_phrases(raw_query)
        
        # Handle operators
        operators, remaining_query = self._extract_operators(remaining_query)
        
        # Process remaining terms
        processed_terms = self.text_processor.process_text(remaining_query)
        
        # Combine all processed elements
        return {
            'original_query': raw_query,
            'processed_terms': processed_terms,
            'phrases': phrases,
            'operators': operators,
            'query_type': query_type,
            'intent': intent,
            'filters': self._extract_filters(raw_query)
        }
        
    def _detect_query_type(self, query):
        """Detect the type of query"""
        query_lower = query.lower()
        
        if any(op in query_lower for op in ['and', 'or', 'not']):
            return 'boolean'
        elif '"' in query:
            return 'phrase'
        elif query.startswith('site:') or 'filetype:' in query:
            return 'filtered'
        elif query.endswith('?') or query.startswith(('what', 'how', 'when', 'where', 'why', 'who')):
            return 'question'
        else:
            return 'simple'
            
    def _detect_intent(self, query):
        """Detect user intent from query"""
        query_lower = query.lower()
        
        # Navigational intent
        navigational_patterns = [
            r'\b(facebook|twitter|instagram|youtube|amazon|google)\b',
            r'\b(login|sign in|homepage|official site)\b'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in navigational_patterns):
            return 'navigational'
            
        # Transactional intent
        transactional_patterns = [
            r'\b(buy|purchase|order|price|cost|cheap|discount|deal)\b',
            r'\b(download|install|get|free)\b'
        ]
        
        if any(re.search(pattern, query_lower) for pattern in transactional_patterns):
            return 'transactional'
            
        # Informational intent (questions)
        if query.endswith('?') or query_lower.startswith(('what', 'how', 'when', 'where', 'why', 'who')):
            return 'informational'
            
        return 'informational'  # Default
        
    def _extract_phrases(self, query):
        """Extract quoted phrases from query"""
        phrases = []
        remaining_query = query
        
        # Find quoted phrases
        phrase_pattern = r'"([^"]*)"'
        matches = re.finditer(phrase_pattern, query)
        
        for match in matches:
            phrase = match.group(1).strip()
            if phrase:
                # Process phrase terms but keep them together
                phrase_terms = self.text_processor.process_text(phrase)
                phrases.append(phrase_terms)
                
            # Remove from remaining query
            remaining_query = remaining_query.replace(match.group(0), ' ')
            
        return phrases, remaining_query.strip()
        
    def _extract_operators(self, query):
        """Extract boolean operators from query"""
        operators = []
        remaining_query = query
        
        # Find operators (case insensitive)
        operator_pattern = r'\b(AND|OR|NOT)\b'
        matches = re.finditer(operator_pattern, query, re.IGNORECASE)
        
        for match in matches:
            operator = match.group(1).upper()
            operators.append(operator)
            # Remove from remaining query
            remaining_query = remaining_query.replace(match.group(0), ' ')
            
        return operators, remaining_query.strip()
        
    def _extract_filters(self, query):
        """Extract search filters from query"""
        filters = {}
        
        # Site filter (site:example.com)
        site_match = re.search(r'site:([^\s]+)', query, re.IGNORECASE)
        if site_match:
            filters['site'] = site_match.group(1)
            
        # Filetype filter (filetype:pdf)
        filetype_match = re.search(r'filetype:([^\s]+)', query, re.IGNORECASE)
        if filetype_match:
            filters['filetype'] = filetype_match.group(1)
            
        # Date filters
        date_patterns = {
            'last_day': r'\b(today|yesterday)\b',
            'last_week': r'\blast week\b',
            'last_month': r'\blast month\b',
            'last_year': r'\blast year\b'
        }
        
        for period, pattern in date_patterns.items():
            if re.search(pattern, query, re.IGNORECASE):
                filters['date'] = period
                break
                
        return filters
        
    def expand_query(self, processed_query):
        """Expand query with synonyms and related terms"""
        expanded_terms = processed_query['processed_terms'].copy()
        
        # Simple synonym expansion (in practice, use WordNet or custom synonym database)
        synonyms = {
            'car': ['vehicle', 'automobile', 'auto'],
            'house': ['home', 'residence', 'property'],
            'job': ['work', 'employment', 'career'],
            'phone': ['mobile', 'smartphone', 'cell']
        }
        
        for term in processed_query['processed_terms']:
            if term in synonyms:
                expanded_terms.extend(synonyms[term])
                
        return expanded_terms
        
    def correct_spelling(self, query):
        """Basic spelling correction"""
        # Simple implementation - in practice use advanced spelling correctors
        common_corrections = {
            'teh': 'the',
            'adn': 'and',
            'recieve': 'receive',
            'seperate': 'separate',
            'definately': 'definitely'
        }
        
        corrected_query = query
        for mistake, correction in common_corrections.items():
            corrected_query = re.sub(r'\b' + mistake + r'\b', correction, corrected_query, flags=re.IGNORECASE)
            
        return corrected_query
        
    def get_query_suggestions(self, partial_query):
        """Generate query suggestions based on partial input"""
        # This would typically use query logs and popularity data
        suggestions = []
        
        # Simple prefix-based suggestions
        common_queries = [
            'python programming',
            'machine learning',
            'web development',
            'data science',
            'artificial intelligence',
            'software engineering'
        ]
        
        partial_lower = partial_query.lower()
        for query in common_queries:
            if query.startswith(partial_lower):
                suggestions.append(query)
                
        return suggestions[:5]  # Return top 5 suggestions
