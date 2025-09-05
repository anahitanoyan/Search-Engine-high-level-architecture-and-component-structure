from flask import Flask, request, jsonify, render_template_string
import time
from ranker.relevance_scorer import RelevanceScorer
from query_processor.query_parser import QueryParser
from indexer.inverted_index import InvertedIndex
from ranker.tf_idf import TFIDFScorer
from ranker.pagerank import PageRank
from config.settings import Config
import logging

app = Flask(__name__)
logger = logging.getLogger(__name__)

class SearchAPI:
    def __init__(self):
        # Initialize components
        self.inverted_index = InvertedIndex()
        self.query_parser = QueryParser()
