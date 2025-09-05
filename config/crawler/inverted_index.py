from collections import defaultdict
import json
import pickle
from typing import Dict, List, Tuple

class InvertedIndex:
    def __init__(self):
        self.index = defaultdict(list)  # term -> [(doc_id, tf, positions)]
        self.document_freq = defaultdict(int)  # term -> document frequency
        self.total_docs = 0
        self.doc_lengths = {}  # doc_id -> document length
        
    def add_document(self, doc_id: str, tokens: List[str]):
        """Add a document to the inverted index"""
        if doc_id in self.doc_lengths:
            return  # Document already indexed
            
        # Calculate term frequencies and positions
        term_positions = defaultdict(list)
        term_freq = defaultdict(int)
        
        for position, token in enumerate(tokens):
            if len(token) >= 2:  # Ignore very short terms
                term_freq[token] += 1
                term_positions[token].append(position)
        
        # Add to inverted index
        for term, freq in term_freq.items():
            positions = term_positions[term]
            self.index[term].append((doc_id, freq, positions))
            
        # Update document frequency
        unique_terms = set(term_freq.keys())
        for term in unique_terms:
            self.document_freq[term] += 1
            
        # Store document length
        self.doc_lengths[doc_id] = len(tokens)
        self.total_docs += 1
        
    def search(self, terms: List[str]) -> Dict[str, List[Tuple]]:
        """Search for documents containing the terms"""
        results = {}
        for term in terms:
            if term in self.index:
                results[term] = self.index[term]
            else:
                results[term] = []
        return results
        
    def get_document_frequency(self, term: str) -> int:
        """Get document frequency for a term"""
        return self.document_freq.get(term, 0)
        
    def get_term_frequency(self, term: str, doc_id: str) -> int:
        """Get term frequency in a specific document"""
        if term in self.index:
            for doc, tf, positions in self.index[term]:
                if doc == doc_id:
                    return tf
        return 0
        
    def get_document_length(self, doc_id: str) -> int:
        """Get the length of a document"""
        return self.doc_lengths.get(doc_id, 0)
        
    def save_to_file(self, filepath: str):
        """Save index to file"""
        index_data = {
            'index': dict(self.index),
            'document_freq': dict(self.document_freq),
            'total_docs': self.total_docs,
            'doc_lengths': self.doc_lengths
        }
        
        with open(filepath, 'wb') as f:
            pickle.dump(index_data, f)
            
    def load_from_file(self, filepath: str):
        """Load index from file"""
        with open(filepath, 'rb') as f:
            index_data = pickle.load(f)
            
        self.index = defaultdict(list, index_data['index'])
        self.document_freq = defaultdict(int, index_data['document_freq'])
        self.total_docs = index_data['total_docs']
        self.doc_lengths = index_data['doc_lengths']
        
    def get_stats(self):
        """Get index statistics"""
        return {
            'total_documents': self.total_docs,
            'unique_terms': len(self.index),
            'total_postings': sum(len(postings) for postings in self.index.values()),
            'average_doc_length': sum(self.doc_lengths.values()) / len(self.doc_lengths) if self.doc_lengths else 0
        }
