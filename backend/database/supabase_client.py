"""
Supabase client and database utilities
Handles all database operations with vector similarity search
"""

from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from config import settings
import numpy as np


class SupabaseDB:
    """Supabase database client with vector search capabilities"""

    def __init__(self):
        self.client: Client = create_client(
            settings.supabase_url, settings.supabase_service_role_key
        )

    # ============================================================================
    # PRODUCT OPERATIONS
    # ============================================================================

    def get_product_by_id(self, product_id: str) -> Optional[Dict[str, Any]]:
        """Get product by item_id"""
        response = (
            self.client.table("products").select("*").eq("item_id", product_id).execute()
        )
        return response.data[0] if response.data else None

    def get_product_by_url(self, product_url: str) -> Optional[Dict[str, Any]]:
        """Get product by product_url"""
        response = (
            self.client.table("products")
            .select("*")
            .eq("product_url", product_url)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_product_reviews(self, product_id: str, limit: int = 50) -> List[Dict[str, Any]]:
        """Get all reviews for a specific product"""
        response = (
            self.client.table("reviews")
            .select("*")
            .eq("item_id", product_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def find_similar_products(
        self, product_embedding: List[float], limit: int = 5, threshold: float = 0.7
    ) -> List[Dict[str, Any]]:
        """
        Find similar products using vector similarity search
        Uses pgvector cosine similarity
        """
        # Convert embedding to numpy array for processing
        query_embedding = np.array(product_embedding)

        # Execute vector similarity search using RPC function
        response = self.client.rpc(
            "match_products",
            {
                "query_embedding": query_embedding.tolist(),
                "match_threshold": threshold,
                "match_count": limit,
            },
        ).execute()

        return response.data if response.data else []

    def get_similar_products_with_reviews(
        self, product_embedding: List[float], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """Get similar products that have reviews"""
        similar_products = self.find_similar_products(product_embedding, limit=limit)

        # Filter products that have reviews
        products_with_reviews = []
        for product in similar_products:
            reviews = self.get_product_reviews(product["item_id"], limit=10)
            if reviews:
                product["reviews"] = reviews
                products_with_reviews.append(product)

        return products_with_reviews

    # ============================================================================
    # USER OPERATIONS
    # ============================================================================

    def get_user_by_id(self, user_id: str) -> Optional[Dict[str, Any]]:
        """Get user by user_id"""
        response = (
            self.client.table("users").select("*").eq("user_id", user_id).execute()
        )
        return response.data[0] if response.data else None

    def get_user_by_email(self, email: str) -> Optional[Dict[str, Any]]:
        """Get user by email_id"""
        response = self.client.table("users").select("*").eq("email_id", email).execute()
        return response.data[0] if response.data else None

    def get_user_transactions(
        self, user_id: str, limit: int = 10
    ) -> List[Dict[str, Any]]:
        """Get user's transaction history with product details"""
        response = (
            self.client.table("transactions")
            .select("*, products(*)")
            .eq("user_id", user_id)
            .order("order_date", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def get_user_reviews(self, user_id: str, limit: int = 20) -> List[Dict[str, Any]]:
        """Get all reviews written by user"""
        response = (
            self.client.table("reviews")
            .select("*, products(*)")
            .eq("user_id", user_id)
            .order("created_at", desc=True)
            .limit(limit)
            .execute()
        )
        return response.data

    def find_user_similar_product_purchases(
        self, user_id: str, product_embedding: List[float], limit: int = 5
    ) -> List[Dict[str, Any]]:
        """
        Find user's purchases of similar products using embeddings
        Returns transactions with product details
        """
        # Get user's transaction history
        transactions = self.get_user_transactions(user_id, limit=50)

        if not transactions:
            return []

        # Calculate similarity for each transaction's product
        query_embedding = np.array(product_embedding)
        similar_transactions = []

        for txn in transactions:
            if txn.get("products") and txn["products"].get("embeddings"):
                # Parse embedding if it's a JSON string
                emb_data = txn["products"]["embeddings"]
                if isinstance(emb_data, str):
                    import json
                    emb_data = json.loads(emb_data)
                product_emb = np.array(emb_data)
                similarity = np.dot(query_embedding, product_emb) / (
                    np.linalg.norm(query_embedding) * np.linalg.norm(product_emb)
                )

                if similarity >= settings.similarity_threshold:
                    txn["similarity_score"] = float(similarity)
                    similar_transactions.append(txn)

        # Sort by similarity and return top matches
        similar_transactions.sort(key=lambda x: x["similarity_score"], reverse=True)
        return similar_transactions[:limit]

    # ============================================================================
    # SURVEY OPERATIONS
    # ============================================================================

    def create_survey_session(
        self, user_id: str, item_id: str, metadata: Dict[str, Any]
    ) -> str:
        """
        Create a new survey session and return session_id

        Creates a placeholder transaction for this survey session since
        the survey_sessions table requires a transaction_id reference.
        """
        from datetime import datetime, timedelta
        import uuid

        # Create a placeholder transaction for this survey session
        # This represents the survey flow, not an actual purchase yet
        order_date = datetime.now()
        transaction_data = {
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "item_id": item_id,
            "order_date": order_date.isoformat(),
            "expected_delivery_date": (order_date + timedelta(days=5)).isoformat(),
            "original_price": 0.00,  # Placeholder - survey not tied to actual purchase
            "retail_price": 0.00,
            "transaction_status": "survey_pending",  # Special status for survey flows
        }

        txn_response = self.client.table("transactions").insert(transaction_data).execute()
        transaction_id = txn_response.data[0]["transaction_id"] if txn_response.data else None

        if not transaction_id:
            raise Exception("Failed to create placeholder transaction for survey session")

        # Now create the survey session with the transaction_id
        response = (
            self.client.table("survey_sessions")
            .insert(
                {
                    "user_id": user_id,
                    "transaction_id": transaction_id,
                    "session_context": metadata,  # Use session_context instead of metadata
                }
            )
            .execute()
        )
        return response.data[0]["session_id"] if response.data else None

    def get_survey_session(self, session_id: str) -> Optional[Dict[str, Any]]:
        """Get survey session by ID"""
        response = (
            self.client.table("survey_sessions")
            .select("*")
            .eq("session_id", session_id)
            .execute()
        )
        return response.data[0] if response.data else None

    def update_survey_session(
        self,
        session_id: str,
        conversation_history: List[Dict[str, Any]],
        state: str = "active",
        metadata: Optional[Dict[str, Any]] = None,
    ) -> bool:
        """Update survey session with new conversation history and state"""
        # Get current session_context and merge with new data
        session = self.get_survey_session(session_id)
        current_context = session.get("session_context", {}) if session else {}

        # Merge metadata into session_context
        if metadata:
            current_context.update(metadata)

        # Add conversation_history to context
        current_context["conversation_history"] = conversation_history

        update_data = {
            "session_context": current_context,
            "is_completed": (state == "completed"),
            "updated_at": "now()",
        }

        if state == "completed":
            update_data["completed_at"] = "now()"

        response = (
            self.client.table("survey_sessions")
            .update(update_data)
            .eq("session_id", session_id)
            .execute()
        )
        return bool(response.data)

    def save_survey_question(
        self,
        session_id: str,
        question_text: str,
        question_options: List[str],
        explanation: str,
        metadata: Dict[str, Any],
    ) -> str:
        """Save a survey question to the database"""
        # Get session to retrieve required fields
        session = self.get_survey_session(session_id)
        if not session:
            raise ValueError(f"Session not found: {session_id}")

        # Get transaction to get item_id
        transaction_id = session.get("transaction_id")
        txn_response = (
            self.client.table("transactions")
            .select("item_id")
            .eq("transaction_id", transaction_id)
            .execute()
        )
        item_id = txn_response.data[0]["item_id"] if txn_response.data else None

        # Extract question number from metadata
        question_number = metadata.get("index", 0) + 1

        response = (
            self.client.table("survey")
            .insert(
                {
                    "item_id": item_id,
                    "user_id": session.get("user_id"),
                    "transaction_id": transaction_id,
                    "question_number": question_number,
                    "question": question_text,
                    "options_object": {"options": question_options, "explanation": explanation},
                }
            )
            .execute()
        )
        return response.data[0]["question_id"] if response.data else None

    def update_survey_answer(
        self, question_id: str, selected_option: str, response_time_ms: int
    ) -> bool:
        """Update survey question with user's answer"""
        response = (
            self.client.table("survey")
            .update(
                {
                    "selected_option": selected_option,
                    "response_time_ms": response_time_ms,
                    "answered_at": "now()",
                }
            )
            .eq("question_id", question_id)
            .execute()
        )
        return bool(response.data)

    def get_session_questions(self, session_id: str) -> List[Dict[str, Any]]:
        """Get all questions for a survey session"""
        response = (
            self.client.table("survey")
            .select("*")
            .eq("session_id", session_id)
            .order("created_at")
            .execute()
        )
        return response.data

    # ============================================================================
    # REVIEW OPERATIONS
    # ============================================================================

    def save_generated_review(
        self,
        user_id: str,
        item_id: str,
        review_text: str,
        rating: int,
        sentiment_label: str,
        metadata: Dict[str, Any],
    ) -> str:
        """Save generated review to database"""
        import uuid
        from datetime import datetime

        # Create a transaction for this review
        transaction_data = {
            "transaction_id": str(uuid.uuid4()),
            "user_id": user_id,
            "item_id": item_id,
            "order_date": datetime.now().isoformat(),
            "expected_delivery_date": datetime.now().isoformat(),
            "original_price": 0.00,
            "retail_price": 0.00,
            "transaction_status": "completed",
        }
        txn_response = self.client.table("transactions").insert(transaction_data).execute()
        transaction_id = txn_response.data[0]["transaction_id"] if txn_response.data else None

        if not transaction_id:
            raise Exception("Failed to create transaction for review")

        # Insert review with correct field names from schema
        response = (
            self.client.table("reviews")
            .insert(
                {
                    "user_id": user_id,
                    "item_id": item_id,
                    "transaction_id": transaction_id,
                    "review_text": review_text,
                    "review_stars": rating,  # Correct field name
                    "manual_or_agent_generated": "agent",
                    "review_title": metadata.get("tone", "Generated Review"),
                }
            )
            .execute()
        )
        return response.data[0]["review_id"] if response.data else None


# Global database instance
db = SupabaseDB()
