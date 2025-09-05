import numpy as np
from collections import defaultdict
import pickle
import logging
from config.settings import Config

logger = logging.getLogger(__name__)

class PageRank:
    def __init__(self, damping_factor=0.85, max_iterations=50, tolerance=1e-6):
        self.damping_factor = damping_factor
        self.max_iterations = max_iterations
        self.tolerance = tolerance
        self.graph = defaultdict(set)  # outgoing links
        self.reverse_graph = defaultdict(set)  # incoming links
        self.scores = {}
        self.url_to_id = {}
        self.id_to_url = {}
        self.next_id = 0
        
    def add_link(self, source_url, target_url):
        """Add a link to the graph"""
        source_id = self._get_or_create_id(source_url)
        target_id = self._get_or_create_id(target_url)
        
        self.graph[source_id].add(target_id)
        self.reverse_graph[target_id].add(source_id)
        
    def _get_or_create_id(self, url):
        """Get or create numeric ID for URL"""
        if url not in self.url_to_id:
            self.url_to_id[url] = self.next_id
            self.id_to_url[self.next_id] = url
            self.next_id += 1
        return self.url_to_id[url]
        
    def calculate_pagerank(self):
        """Calculate PageRank scores using power iteration method"""
        if not self.graph:
            logger.warning("Empty graph, cannot calculate PageRank")
            return
            
        n = len(self.url_to_id)
        logger.info(f"Calculating PageRank for {n} pages")
        
        # Initialize scores uniformly
        scores = np.ones(n) / n
        
        # Create transition matrix
        transition_matrix = self._build_transition_matrix(n)
        
        # Power iteration
        for iteration in range(self.max_iterations):
            new_scores = self._pagerank_iteration(scores, transition_matrix, n)
            
            # Check convergence
            diff = np.linalg.norm(new_scores - scores, 1)
            if diff < self.tolerance:
                logger.info(f"PageRank converged after {iteration + 1} iterations")
                break
                
            scores = new_scores
            
        # Store final scores
        for node_id, score in enumerate(scores):
            if node_id < len(self.id_to_url):
                url = self.id_to_url[node_id]
                self.scores[url] = score
                
        logger.info(f"PageRank calculation completed. Top score: {max(self.scores.values()):.6f}")
        
    def _build_transition_matrix(self, n):
        """Build the transition matrix for PageRank"""
        matrix = np.zeros((n, n))
        
        for source_id in range(n):
            outgoing_links = self.graph.get(source_id, set())
            
            if outgoing_links:
                # Distribute probability equally among outgoing links
                prob = 1.0 / len(outgoing_links)
                for target_id in outgoing_links:
                    if target_id < n:
                        matrix[target_id][source_id] = prob
            else:
                # Dead-end handling: distribute probability to all pages
                matrix[:, source_id] = 1.0 / n
                
        return matrix
        
    def _pagerank_iteration(self, scores, transition_matrix, n):
        """Single iteration of PageRank calculation"""
        # Apply damping factor
        damped_scores = self.damping_factor * np.dot(transition_matrix, scores)
        
        # Add random jump probability
        random_jump = (1 - self.damping_factor) / n
        new_scores = damped_scores + random_jump
        
        return new_scores
        
    def get_score(self, url):
        """Get PageRank score for a URL"""
        return self.scores.get(url, 0.0)
        
    def get_top_pages(self, n=10):
        """Get top N pages by PageRank score"""
        sorted_pages = sorted(self.scores.items(), key=lambda x: x[1], reverse=True)
        return sorted_pages[:n]
        
    def save_scores(self, filepath):
        """Save PageRank scores to file"""
        with open(filepath, 'wb') as f:
            pickle.dump({
                'scores': self.scores,
                'url_to_id': self.url_to_id,
                'id_to_url': self.id_to_url,
                'graph': dict(self.graph),
                'reverse_graph': dict(self.reverse_graph)
            }, f)
            
    def load_scores(self, filepath):
        """Load PageRank scores from file"""
        try:
            with open(filepath, 'rb') as f:
                data = pickle.load(f)
                self.scores = data['scores']
                self.url_to_id = data['url_to_id']
                self.id_to_url = data['id_to_url']
                self.graph = defaultdict(set, data['graph'])
                self.reverse_graph = defaultdict(set, data['reverse_graph'])
                self.next_id = len(self.url_to_id)
                logger.info(f"Loaded PageRank scores for {len(self.scores)} pages")
        except FileNotFoundError:
            logger.warning(f"PageRank file not found: {filepath}")
        except Exception as e:
            logger.error(f"Error loading PageRank scores: {e}")
            
    def get_graph_stats(self):
        """Get statistics about the link graph"""
        total_nodes = len(self.url_to_id)
        total_edges = sum(len(links) for links in self.graph.values())
        
        # Calculate average degree
        avg_out_degree = total_edges / total_nodes if total_nodes > 0 else 0
        
        # Find nodes with no outgoing links (dead ends)
        dead_ends = sum(1 for node_id in range(total_nodes) 
                       if len(self.graph.get(node_id, set())) == 0)
        
        # Find nodes with no incoming links
        no_incoming = sum(1 for node_id in range(total_nodes)
                         if len(self.reverse_graph.get(node_id, set())) == 0)
        
        return {
            'total_nodes': total_nodes,
            'total_edges': total_edges,
            'average_out_degree': avg_out_degree,
            'dead_ends': dead_ends,
            'no_incoming_links': no_incoming,
            'density': total_edges / (total_nodes * total_nodes) if total_nodes > 0 else 0
        }
        
    def personalized_pagerank(self, seed_urls, alpha=0.15):
        """Calculate personalized PageRank for specific seed URLs"""
        if not seed_urls or not self.url_to_id:
            return {}
            
        n = len(self.url_to_id)
        
        # Create personalization vector
        personalization = np.zeros(n)
        seed_ids = []
        
        for url in seed_urls:
            if url in self.url_to_id:
                seed_ids.append(self.url_to_id[url])
                
        if not seed_ids:
            logger.warning("No valid seed URLs found")
            return {}
            
        # Distribute personalization equally among seed pages
        for seed_id in seed_ids:
            personalization[seed_id] = 1.0 / len(seed_ids)
            
        # Initialize scores
        scores = personalization.copy()
        transition_matrix = self._build_transition_matrix(n)
        
        # Power iteration with personalization
        for iteration in range(self.max_iterations):
            new_scores = ((1 - alpha) * np.dot(transition_matrix, scores) + 
                         alpha * personalization)
            
            # Check convergence
            diff = np.linalg.norm(new_scores - scores, 1)
            if diff < self.tolerance:
                break
                
            scores = new_scores
            
        # Convert to dictionary
        personalized_scores = {}
        for node_id, score in enumerate(scores):
            if node_id < len(self.id_to_url):
                url = self.id_to_url[node_id]
                personalized_scores[url] = score
                
        return personalized_scores
