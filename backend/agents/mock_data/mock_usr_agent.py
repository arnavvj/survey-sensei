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
        form_data: Dict[str, Any],
        generate_embeddings: bool = False
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
            'is_main_user': True,  # Flag for form submission user (survey target)
            'created_at': datetime.now().isoformat(),
            'updated_at': datetime.now().isoformat(),
        }

        # Generate embeddings if requested
        # Uses fields: user_name, age, base_location, base_zip, gender
        if generate_embeddings:
            embedding_text = self.build_user_embedding_text(user)
            user['embeddings'] = self.generate_single_embedding(embedding_text)
        else:
            user['embeddings'] = None

        return user

    def generate_mock_users(
        self,
        main_user: Dict[str, Any],
        count: int = 10,
        generate_embeddings: bool = False
    ) -> List[Dict[str, Any]]:
        """
        Generate mock users with diverse demographics

        Args:
            main_user: Main user from form (for demographic context)
            count: Number of mock users to generate

        Returns:
            List of mock user dictionaries
        """
        import hashlib
        import time

        # Add timestamp-based seed for variation across runs
        seed = hashlib.md5(f"{time.time()}{count}".encode()).hexdigest()[:8]

        system_prompt = """You are a demographic data engineer creating highly diverse, creative user personas for an e-commerce platform.

CRITICAL REQUIREMENTS:
- Generate UNIQUE and VARIED names (avoid repetitive patterns)
- Use diverse naming styles: traditional, modern, multicultural, hyphenated
- Vary ages significantly (spread across 18-75 range, not clustered)
- Include diverse US cities: major metros, mid-size cities, small towns
- Mix coastal, midwest, southern, western locations
- Creative but realistic email patterns (not all firstname.lastname)
- Balance gender distribution

DIVERSITY EXAMPLES:
Names: Mix "Emma Johnson", "Raj Patel", "Maria Garcia", "Tyler Chen", "Jordan Williams"
Emails: Various styles like firstlast@, initial.last@, nickname@, first123@
Ages: Spread from Gen Z (18-24), Millennials (25-40), Gen X (41-56), Boomers (57-75)
Locations: Mix NYC, Austin, Portland, Nashville, Boulder, Boise, Asheville, etc.

Return ONLY valid JSON."""

        # Generate users in batches of 20 to avoid JSON parsing errors
        all_users = []
        batch_size = 20
        remaining = count

        while remaining > 0:
            batch_count = min(batch_size, remaining)

            user_prompt = f"""Generate {batch_count} HIGHLY DIVERSE and UNIQUE user personas.

Uniqueness seed: {seed}-{len(all_users)}

Context (for demographic VARIETY - create users DIFFERENT from this):
Main user age: {main_user['age']}
Main user location: {main_user['base_location']}

Return JSON array with these fields for each user:
[
  {{
    "user_name": "full name (be creative, use diverse cultural backgrounds)",
    "email_id": "realistic email (vary the format/style for each user)",
    "age": age as number (SPREAD across 18-75, avoid clustering),
    "base_location": "City, State format (use VARIED cities across US)",
    "base_zip": "5-digit ZIP code (must match the city)",
    "gender": "Male or Female (balance distribution)"
  }}
]

IMPORTANT: Make each user distinctly DIFFERENT from others. Avoid patterns like all similar ages or all big cities.
Be creative with names (traditional, modern, multicultural mix). Vary email styles. Spread ages widely."""

            response = self._call_llm(
                system_prompt=system_prompt,
                user_prompt=user_prompt,
                max_tokens=1500,  # Higher for multiple users
                temperature=1.0  # Maximum creativity for diverse users
            )

            users_batch = self._parse_json_response(response)

            # Ensure users is a list
            if isinstance(users_batch, dict):
                users_batch = [users_batch]

            all_users.extend(users_batch[:batch_count])
            remaining -= batch_count

        users = all_users

        # Add system fields
        import uuid
        for user in users:
            user['user_id'] = str(uuid.uuid4())
            user['is_main_user'] = False  # Generated mock user (not the survey target)
            user['created_at'] = datetime.now().isoformat()
            user['updated_at'] = datetime.now().isoformat()

            # Generate embeddings if requested
            # Uses fields: user_name, age, base_location, base_zip, gender
            if generate_embeddings:
                embedding_text = self.build_user_embedding_text(user)
                user['embeddings'] = self.generate_single_embedding(embedding_text)
            else:
                user['embeddings'] = None

        return users[:count]
