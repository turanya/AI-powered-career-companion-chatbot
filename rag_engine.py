"""
RAG (Retrieval Augmented Generation) Engine for Asha AI Chatbot
"""

import numpy as np
from typing import List, Dict, Any, Tuple
from sentence_transformers import SentenceTransformer
from sklearn.metrics.pairwise import cosine_similarity
import json
import os

class RAGEngine:
    def __init__(self):
        # Initialize the sentence transformer model for semantic search
        self.model = SentenceTransformer('all-MiniLM-L6-v2')
        self.knowledge_base = {}
        self.embeddings = {}
        self.categories = [
            'careers', 'jobs', 'events', 'mentorship',
            'skills', 'success_stories', 'resources'
        ]
        
    def initialize_knowledge_base(self, data_path: str = 'data/'):
        """Initialize knowledge base from data files"""
        for category in self.categories:
            file_path = os.path.join(data_path, f'{category}.json')
            if os.path.exists(file_path):
                with open(file_path, 'r') as f:
                    self.knowledge_base[category] = json.load(f)
                    
                # Create embeddings for the category content
                self._create_embeddings(category)
    
    def _create_embeddings(self, category: str):
        """Create embeddings for a category's content"""
        texts = []
        metadata = []
        
        if category not in self.knowledge_base:
            return
        
        data = self.knowledge_base[category]
        if not isinstance(data, list):
            # Handle cases where data is wrapped in a container object
            if isinstance(data, dict):
                data = data.get(category, []) or data.get(f"{category}_opportunities", [])
        
        for item in data:
            if not isinstance(item, dict):
                continue
                
            # Create a comprehensive text representation of the item
            text_parts = []
            for k, v in item.items():
                if isinstance(v, (str, int, float)):
                    text_parts.append(str(v))
                elif isinstance(v, list):
                    # Handle lists by joining their string representations
                    text_parts.extend(str(x) for x in v if isinstance(x, (str, int, float)))
            
            text = ' '.join(text_parts)
            if text:
                texts.append(text)
                metadata.append(item)
        
        # Generate embeddings for all texts in the category
        if texts:
            embeddings = self.model.encode(texts, convert_to_tensor=True)
            self.embeddings[category] = {
                'vectors': embeddings,
                'texts': texts,
                'metadata': metadata
            }
    
    def semantic_search(self, query: str, category: str = None, top_k: int = 5) -> List[Dict[str, Any]]:
        """
        Perform semantic search across the knowledge base
        
        Args:
            query: The search query
            category: Optional category to search within
            top_k: Number of results to return
            
        Returns:
            List of relevant documents with their metadata
        """
        # Encode the query
        query_embedding = self.model.encode(query, convert_to_tensor=True)
        
        results = []
        categories_to_search = [category] if category else self.categories
        
        for cat in categories_to_search:
            if cat in self.embeddings:
                # Calculate similarity scores
                similarities = cosine_similarity(
                    query_embedding.reshape(1, -1),
                    self.embeddings[cat]['vectors']
                )[0]
                
                # Get top matches
                top_indices = np.argsort(similarities)[-top_k:][::-1]
                
                # Add results with their metadata and scores
                for idx in top_indices:
                    if similarities[idx] > 0.3:  # Similarity threshold
                        results.append({
                            'category': cat,
                            'content': self.embeddings[cat]['metadata'][idx],
                            'similarity': float(similarities[idx])
                        })
        
        # Sort all results by similarity score
        results.sort(key=lambda x: x['similarity'], reverse=True)
        return results[:top_k]
    
    def generate_response(self, query: str, context: List[Dict[str, Any]]) -> str:
        """
        Generate a response using retrieved context
        
        Args:
            query: User query
            context: Retrieved relevant documents
            
        Returns:
            Generated response
        """
        if not context:
            return "I couldn't find specific information about that. Could you please rephrase your question?"
        
        # Combine relevant information from context
        response_parts = []
        
        for item in context:
            category = item['category']
            content = item['content']
            
            if category == 'jobs':
                response_parts.append(
                    f"I found a relevant job opportunity: {content['title']} at {content['company']}. "
                    f"This is a {content['type']} position in {content['location']}."
                )
            
            elif category == 'events':
                response_parts.append(
                    f"There's an upcoming event: {content['title']} on {content['date']}. "
                    f"It's a {content['type']} event focused on {content['topic']}."
                )
            
            elif category == 'mentorship':
                response_parts.append(
                    f"I found a mentorship opportunity with {content['mentor_name']}, "
                    f"who specializes in {content['specialization']} with {content['experience_years']} years of experience."
                )
            
            elif category == 'success_stories':
                response_parts.append(
                    f"Here's an inspiring story: {content['name']} - {content['title']}. "
                    f"{content['summary']}"
                )
            
            elif category == 'skills':
                response_parts.append(
                    f"You might be interested in developing skills in {content['name']}. "
                    f"This skill is in {content['demand']} demand."
                )
        
        # Combine all parts into a coherent response
        response = " ".join(response_parts)
        
        # Add a relevant call to action
        if response:
            response += "\n\nWould you like more specific information about any of these opportunities?"
        
        return response
    
    def get_contextual_suggestions(self, user_history: List[Dict[str, Any]]) -> List[str]:
        """
        Generate contextual suggestions based on user interaction history
        
        Args:
            user_history: List of previous interactions
            
        Returns:
            List of suggested queries or topics
        """
        suggestions = []
        
        # Analyze recent interactions
        recent_categories = set()
        for interaction in user_history[-5:]:  # Look at last 5 interactions
            if 'category' in interaction:
                recent_categories.add(interaction['category'])
        
        # Generate relevant suggestions
        if 'jobs' in recent_categories:
            suggestions.append("Would you like to explore related career development resources?")
            suggestions.append("I can show you success stories from women in similar roles.")
        
        if 'mentorship' in recent_categories:
            suggestions.append("Would you like to see upcoming events with these mentors?")
            suggestions.append("I can help you find skill development resources in this area.")
        
        if 'events' in recent_categories:
            suggestions.append("Would you like to connect with mentors attending these events?")
            suggestions.append("I can show you job opportunities related to these events.")
        
        if not suggestions:
            suggestions = [
                "Would you like to explore job opportunities?",
                "I can show you upcoming career development events.",
                "Would you like to connect with a mentor?",
                "I can share success stories from women leaders."
            ]
        
        return suggestions[:3]  # Return top 3 suggestions 