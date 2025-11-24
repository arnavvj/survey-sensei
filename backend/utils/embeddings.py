"""
Embedding utilities for vector similarity search
Uses OpenAI text-embedding-3-small model
"""

from openai import OpenAI
from typing import List
from config import settings
import numpy as np


class EmbeddingService:
    """Service for generating embeddings using OpenAI"""

    def __init__(self):
        self.client = OpenAI(api_key=settings.openai_api_key)
        self.model = settings.embedding_model

    def generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding for a single text
        Returns 1536-dimensional vector
        """
        response = self.client.embeddings.create(input=text, model=self.model)
        return response.data[0].embedding

    def generate_embeddings(self, texts: List[str]) -> List[List[float]]:
        """Generate embeddings for multiple texts"""
        response = self.client.embeddings.create(input=texts, model=self.model)
        return [item.embedding for item in response.data]

    def cosine_similarity(self, vec1: List[float], vec2: List[float]) -> float:
        """Calculate cosine similarity between two vectors"""
        v1 = np.array(vec1)
        v2 = np.array(vec2)
        return float(np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2)))


# Global embedding service instance
embedding_service = EmbeddingService()
