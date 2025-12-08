"""
MOCK_USR_MINI_AGENT - User Mock Data Generator
Generates realistic user personas for Product/Customer Context Agents
Uses gpt-4o-mini for cost-effective generation
"""

from typing import List, Dict, Any
import random
from datetime import datetime
from .base import BaseMockAgent


class MockUserAgent(BaseMockAgent):
    """
    Generates mock user personas with realistic demographics
    Creates diverse customer profiles for simulation scenarios
    """

    def generate_main_user(
        self,
        form_data: Dict[str, Any]
    ) -> Dict[str, Any]:
        """
        Generate main user persona from form submission

        Args:
            form_data: Form submission with fields:
                - userName: User's name
                - userEmail: User's email
                - userAge: User's age
                - userLocation: City, State
                - userZip: ZIP code
                - userGender: Male/Female/Other

        Returns:
            User dictionary ready for database insertion
        """
        import uuid

        user = {
            'user_id': str(uuid.uuid4()),
            'user_name': form_data['userName'],
            'email_id': form_data['userEmail'],
            'age': form_data['userAge'],
            'base_location': form_data['userLocation'],
            'base_zip': form_data['userZip'],
            'gender': form_data['userGender'],
            'is_mock': False,  # Real user from form
            'is_main_user': True,  # Flag for form submission user
            'embeddings': None,  # Reserved for future use
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        return user

    def generate_mock_users(
        self,
            main_user: Dict[str, Any],
        count: int = 10
    ) -> List[Dict[str, Any]]:
        """
        Generate mock users with diverse demographics

        Args:
            main_user: Main user from form (for demographic context)
            count: Number of mock users to generate

        Returns:
            List of mock user dictionaries
        """
        system_prompt = """You are a demographic data engineer creating realistic user personas for an e-commerce platform.
Generate diverse users with realistic demographics:
- Mix of ages (18-75)
- Various US locations (cities and ZIP codes)
- Balanced gender distribution
- Realistic name variations

Return ONLY valid JSON."""

        user_prompt = f"""Generate {count} diverse user personas.

Context (for demographic variety):
Main user age: {main_user['age']}
Main user location: {main_user['base_location']}

Return JSON array with these fields for each user:
[
  {{
    "user_name": "full name",
    "email_id": "realistic email address",
    "age": age as number (18-75),
    "base_location": "City, State format",
    "base_zip": "5-digit ZIP code",
    "gender": "Male or Female"
  }}
]

Make them diverse and realistic."""

        response = self._call_llm(
            system_prompt=system_prompt,
            user_prompt=user_prompt,
            max_tokens=1500,  # Higher for multiple users
            temperature=0.9
        )

        users = self._parse_json_response(response)

        # Ensure users is a list
        if isinstance(users, dict):
            users = [users]

        # Add system fields
        import uuid
        for user in users:
            user['user_id'] = str(uuid.uuid4())
            user['is_mock'] = True
            user['is_main_user'] = False
            user['embeddings'] = None
            user['created_at'] = datetime.now().isoformat()
            user['updated_at'] = datetime.now().isoformat()

        return users[:count]
