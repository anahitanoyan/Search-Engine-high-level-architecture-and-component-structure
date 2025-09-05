import math
from typing import List, Dict, Tuple
from indexer.inverted_index import InvertedIndex

class TFIDFScorer:
    def __init__(self, inverted_index: InvertedIndex):
        self.index = inverted_index
        
    def calculate_tf(self, term_freq: int, doc_length: int, method='log_normalized') -> float:
        """Calculate term frequency score"""
        if method == 'raw':
            return term_freq
        elif method == 'log_normalized':
            return 1 + math.log(term_freq) if term_freq > 0 else 0
        elif method == 'double_normalized':
            # Prevent bias towards longer documents
            return 0.5 + (0.5 * term_freq / doc_length) if doc_length > 0 else 0
        else:
            return term_freq
            
    def calculate_idf(self, term: str) -> float:
        """Calculate inverse document frequency"""
        doc_freq = self.index.get_document_frequency(term)
        if doc_freq == 0:
            return 0
            
        return math.log(self.index.total_docs / doc_freq)
        
    def calculate_tfidf(self, term: str, doc_id: str) -> float:
        """Calculate TF-IDF score for a term in a document"""
        tf = self.index.get_term_frequency(term, doc_id)
        if tf == 0:
            return 0
            
        doc_length = self.index.get_document_length(doc_id)
        tf_score = self.calculate_tf(tf, doc_length)
        idf_score = self.calculate_idf(term)
        
        return tf_score * idf_score
        
    def score_document(self, query_terms: List[str], doc_id: str) -> float:
        """Calculate TF-IDF score for a document given query terms"""
        total_score = 0
        
        for term in query_terms:
            tfidf_score = self.calculate_tfidf(term, doc_id)
            total_score += tfidf_score
            
        # Normalize by query length
        return total_score / len(query_terms) if query_terms else 0
        
    def score_documents(self, query_terms: List[str], candidate_docs: List[str]) -> List[Tuple[str, float]]:
        """Score multiple documents for query terms"""
        scored_docs = []
        
        for doc_id in candidate_docs:
            score = self.score_document(query_terms, doc_id)
            if score > 0:
                scored_docs.append((doc_id, score))
                
        # Sort by score descending
        return sorted(scored_docs, key=lambda x: x[1], reverse=True)
        
    def get_candidate_documents(self, query_terms: List[str]) -> set:
        """Get all documents that contain at least one query term"""
        candidate_docs = set()
        
        for term in query_terms:
            search_results = self.index.search([term])
            if term in search_results:
                for doc_id, tf, positions in search_results[term]:
                    candidate_docs.add(doc_id)
                    
        return candidate_docs
