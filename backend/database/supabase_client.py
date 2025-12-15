"""
Supabase client and database utilities
Handles all database operations with vector similarity search
"""

from supabase import create_client, Client
from typing import List, Dict, Any, Optional
from config import settings
import numpy as np
import asyncio


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
    # CLEANUP OPERATIONS
    # ============================================================================

    def cleanup_mock_data(self) -> Dict[str, int]:
        """
        Delete ALL data from database for clean testing between runs

        This deletes:
        - All survey sessions
        - All reviews
        - All transactions
        - All users (mock AND main users from previous runs)
        - All products (mock AND main products from previous runs)

        This ensures a completely fresh start for each test run.

        Returns:
            Dictionary with counts of deleted records per table
        """
        deleted_counts = {}

        try:
            # STEP 1: Delete all survey sessions
            survey_sessions_resp = self.client.table("survey_sessions").delete().neq("session_id", "00000000-0000-0000-0000-000000000000").execute()
            deleted_counts['survey_sessions'] = len(survey_sessions_resp.data) if survey_sessions_resp.data else 0

            # STEP 2: Delete ALL reviews (cascade will handle this, but explicit is better)
            reviews_resp = self.client.table("reviews").delete().neq("review_id", "00000000-0000-0000-0000-000000000000").execute()
            deleted_counts['reviews'] = len(reviews_resp.data) if reviews_resp.data else 0

            # STEP 3: Delete ALL transactions
            txn_resp = self.client.table("transactions").delete().neq("transaction_id", "00000000-0000-0000-0000-000000000000").execute()
            deleted_counts['transactions'] = len(txn_resp.data) if txn_resp.data else 0

            # STEP 4: Delete ALL users (including previous main users)
            users_resp = self.client.table("users").delete().neq("user_id", "00000000-0000-0000-0000-000000000000").execute()
            deleted_counts['users'] = len(users_resp.data) if users_resp.data else 0

            # STEP 5: Delete ALL products (including previous main products)
            products_resp = self.client.table("products").delete().neq("item_id", "DUMMY_ITEM_ID").execute()
            deleted_counts['products'] = len(products_resp.data) if products_resp.data else 0

        except Exception as e:
            print(f"Warning during cleanup: {str(e)}")

        return deleted_counts

    # ============================================================================
    # PRODUCTS OPERATIONS
    # ============================================================================

    def insert_products_batch(self, products: List[Dict[str, Any]]) -> int:
        """
        Batch insert/upsert products into database

        Args:
            products: List of product dictionaries

        Returns:
            Number of products inserted
        """
        if not products:
            return 0

        try:
            response = self.client.table("products").upsert(
                products,
                on_conflict="item_id"
            ).execute()
            return len(products)
        except Exception as e:
            print(f"Failed to insert products: {str(e)}")
            raise

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

    def get_user_transaction_for_product(
        self, user_id: str, item_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get user's transaction for a specific product"""
        response = (
            self.client.table("transactions")
            .select("*, products(*)")
            .eq("user_id", user_id)
            .eq("item_id", item_id)
            .order("order_date", desc=True)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_review_by_transaction_id(
        self, transaction_id: str
    ) -> Optional[Dict[str, Any]]:
        """Get review for a specific transaction"""
        response = (
            self.client.table("reviews")
            .select("*")
            .eq("transaction_id", transaction_id)
            .limit(1)
            .execute()
        )
        return response.data[0] if response.data else None

    def get_reviews_by_transaction_ids(
        self, transaction_ids: List[str]
    ) -> List[Dict[str, Any]]:
        """Get reviews for multiple transactions"""
        if not transaction_ids:
            return []
        response = (
            self.client.table("reviews")
            .select("*")
            .in_("transaction_id", transaction_ids)
            .execute()
        )
        return response.data

    def insert_users_batch(self, users: List[Dict[str, Any]]) -> int:
        """
        Batch insert/upsert users into database

        Args:
            users: List of user dictionaries

        Returns:
            Number of users inserted
        """
        if not users:
            return 0

        try:
            response = self.client.table("users").upsert(
                users,
                on_conflict="email_id"  # Use email_id since it has UNIQUE constraint
            ).execute()
            return len(users)
        except Exception as e:
            print(f"Failed to insert users: {str(e)}")
            raise

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

    def insert_transactions_batch(self, transactions: List[Dict[str, Any]]) -> int:
        """
        Batch insert/upsert transactions into database

        Args:
            transactions: List of transaction dictionaries

        Returns:
            Number of transactions inserted
        """
        if not transactions:
            return 0

        try:
            response = self.client.table("transactions").upsert(
                transactions,
                on_conflict="transaction_id"
            ).execute()
            return len(transactions)
        except Exception as e:
            print(f"Failed to insert transactions: {str(e)}")
            raise

    def insert_reviews_batch(self, reviews: List[Dict[str, Any]]) -> int:
        """
        Batch insert/upsert reviews into database

        Args:
            reviews: List of review dictionaries

        Returns:
            Number of reviews inserted
        """
        if not reviews:
            return 0

        try:
            response = self.client.table("reviews").upsert(
                reviews,
                on_conflict="review_id"
            ).execute()
            return len(reviews)
        except Exception as e:
            print(f"Failed to insert reviews: {str(e)}")
            raise

    # ============================================================================
    # SURVEY OPERATIONS - NEW SCHEMA
    # ============================================================================

    def create_survey_session(
        self,
        user_id: str,
        item_id: str,
        transaction_id: str,
        product_context: Dict[str, Any],
        customer_context: Dict[str, Any]
    ) -> str:
        """
        Create survey session with new schema (SMP → SVP transition)

        Populates agent contexts immediately at session start.
        questions_and_answers, metrics populated at completion.

        Args:
            user_id: User UUID
            item_id: Product item_id
            transaction_id: Existing or created transaction UUID
            product_context: ProductContext agent output (JSONB)
            customer_context: CustomerContext agent output (JSONB)

        Returns:
            session_id: Created session UUID
        """
        response = self.client.table("survey_sessions").insert({
            "user_id": user_id,
            "item_id": item_id,
            "transaction_id": transaction_id,
            "product_context": product_context,  # JSONB - frozen after start
            "customer_context": customer_context  # JSONB - frozen after start
        }).execute()

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

    def update_review_options(
        self,
        session_id: str,
        review_options: List[Dict[str, Any]],
        sentiment_band: str
    ) -> bool:
        """
        Update review_options JSONB field with generated review options

        Args:
            session_id: Session UUID
            review_options: List of review option dicts (review_title, review_text, review_stars, tone, highlights)
            sentiment_band: Sentiment classification (good/okay/bad)

        Returns:
            bool: True if update successful
        """
        response = (
            self.client.table("survey_sessions")
            .update({
                "review_options": {
                    "options": review_options,
                    "sentiment_band": sentiment_band
                }
            })
            .eq("session_id", session_id)
            .execute()
        )
        return bool(response.data)

    def update_session_context(
        self,
        session_id: str,
        session_context: Dict[str, Any]
    ) -> bool:
        """
        Update session_context JSONB field with complete survey agent state

        Called at survey completion or abortion to store final state.

        Args:
            session_id: Session UUID
            session_context: Complete survey agent state (answers, questions, conversation_history, etc.)

        Returns:
            bool: True if update successful
        """
        response = (
            self.client.table("survey_sessions")
            .update({"session_context": session_context})
            .eq("session_id", session_id)
            .execute()
        )
        return bool(response.data)

    def complete_survey_session(
        self,
        session_id: str,
        questions_and_answers: List[Dict[str, Any]]
    ) -> bool:
        """
        Complete survey session with final Q&A

        Populates questions_and_answers JSONB and marks survey complete.
        Called when survey reaches completion (not aborted).

        Args:
            session_id: Session UUID
            questions_and_answers: List of Q&A dicts (question_number, question_text, selected_option, timestamp)

        Returns:
            bool: True if update successful
        """
        response = (
            self.client.table("survey_sessions")
            .update({"questions_and_answers": questions_and_answers})
            .eq("session_id", session_id)
            .execute()
        )
        return bool(response.data)

    # ASYNC EVENT LOGGING (FIRE-AND-FORGET)

    def insert_survey_detail_sync(
        self,
        session_id: str,
        event_type: str,
        event_detail: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Synchronous survey event insertion

        Called by async wrapper for fire-and-forget logging.
        Errors are caught and logged but don't crash user flow.

        Args:
            session_id: Session UUID
            event_type: Event type (question_generated, answer_submitted, etc.)
            event_detail: Optional JSONB event data (None for survey_incomplete/survey_aborted)

        Returns:
            detail_id: Created event UUID or None if failed
        """
        try:
            response = self.client.table("survey_details").insert({
                "session_id": session_id,
                "event_type": event_type,
                "event_detail": event_detail  # Can be None
            }).execute()
            return response.data[0]["detail_id"] if response.data else None
        except Exception as e:
            print(f"Failed to log survey event ({event_type}): {e}")
            return None

    async def insert_survey_detail_async(
        self,
        session_id: str,
        event_type: str,
        event_detail: Optional[Dict[str, Any]] = None
    ) -> Optional[str]:
        """
        Async wrapper for survey event logging

        Uses asyncio.to_thread to run sync Supabase call without blocking.
        Fire-and-forget pattern - errors logged but don't block user flow.

        Args:
            session_id: Session UUID
            event_type: Event type enum value
            event_detail: Optional event data

        Returns:
            detail_id: Created event UUID or None
        """
        return await asyncio.to_thread(
            self.insert_survey_detail_sync,
            session_id,
            event_type,
            event_detail
        )

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
        """
        Save generated review to database with embeddings

        Uses EXISTING transaction_id (created during data engineering SMP→SVP)
        """
        from utils.embeddings import embedding_service

        # Use existing transaction_id from metadata (NOT creating a new one!)
        transaction_id = metadata.get("transaction_id")
        if not transaction_id:
            raise ValueError(
                "transaction_id is required in metadata. "
                "Review must be linked to existing transaction created during data engineering."
            )

        # Generate embedding for the review text
        review_embedding = embedding_service.generate_embedding(review_text)

        # Insert review with embeddings and correct field names from schema
        response = (
            self.client.table("reviews")
            .insert(
                {
                    "user_id": user_id,
                    "item_id": item_id,
                    "transaction_id": transaction_id,  # Uses existing transaction from data engineering
                    "review_text": review_text,
                    "review_stars": rating,
                    "source": "user_survey",  # Review submitted via survey (user selected from AI-generated options)
                    "manual_or_agent_generated": "agent",  # AI-generated text, user-selected
                    "review_title": metadata.get("review_title", "Product Review"),  # Use title from review option
                    "embeddings": review_embedding,
                }
            )
            .execute()
        )
        return response.data[0]["review_id"] if response.data else None


# Global database instance
db = SupabaseDB()
