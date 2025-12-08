"""
Caching utility for MOCK_DATA_MINI_AGENT framework
Saves generated data to avoid regeneration and reduce costs
"""

import json
import hashlib
import logging
from pathlib import Path
from typing import Dict, Any, Optional
from datetime import datetime, timedelta

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MockDataCache:
    """
    File-based caching system for generated mock data
    Stores data locally to avoid redundant LLM calls
    """

    def __init__(self, cache_dir: str = ".mock_data_cache", ttl_hours: int = 24):
        """
        Initialize cache

        Args:
            cache_dir: Directory to store cache files
            ttl_hours: Time-to-live for cache entries in hours
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(exist_ok=True)
        self.ttl = timedelta(hours=ttl_hours)

    def _generate_cache_key(self, **kwargs) -> str:
        """
        Generate unique cache key from parameters

        Args:
            **kwargs: Parameters to hash

        Returns:
            MD5 hash of sorted parameters
        """
        # Sort keys for consistent hashing
        sorted_params = json.dumps(kwargs, sort_keys=True)
        return hashlib.md5(sorted_params.encode()).hexdigest()

    def _get_cache_path(self, cache_key: str) -> Path:
        """Get file path for cache key"""
        return self.cache_dir / f"{cache_key}.json"

    def get(self, **kwargs) -> Optional[Dict[str, Any]]:
        """
        Retrieve cached data

        Args:
            **kwargs: Parameters to identify cache entry

        Returns:
            Cached data if found and valid, None otherwise
        """
        cache_key = self._generate_cache_key(**kwargs)
        cache_path = self._get_cache_path(cache_key)

        if not cache_path.exists():
            logger.debug(f"Cache miss for key: {cache_key}")
            return None

        try:
            with open(cache_path, 'r', encoding='utf-8') as f:
                cache_data = json.load(f)

            # Check TTL
            cached_at = datetime.fromisoformat(cache_data['cached_at'])
            if datetime.now() - cached_at > self.ttl:
                logger.info(f"Cache expired for key: {cache_key}")
                cache_path.unlink()  # Delete expired cache
                return None

            logger.info(f"Cache hit for key: {cache_key}")
            return cache_data['data']

        except Exception as e:
            logger.warning(f"Failed to read cache for key {cache_key}: {e}")
            return None

    def set(self, data: Dict[str, Any], **kwargs) -> None:
        """
        Store data in cache

        Args:
            data: Data to cache
            **kwargs: Parameters to identify cache entry
        """
        cache_key = self._generate_cache_key(**kwargs)
        cache_path = self._get_cache_path(cache_key)

        cache_entry = {
            'cached_at': datetime.now().isoformat(),
            'params': kwargs,
            'data': data
        }

        try:
            with open(cache_path, 'w', encoding='utf-8') as f:
                json.dump(cache_entry, f, indent=2)
            logger.info(f"Cached data for key: {cache_key}")
        except Exception as e:
            logger.warning(f"Failed to write cache for key {cache_key}: {e}")

    def clear(self) -> int:
        """
        Clear all cache entries

        Returns:
            Number of entries cleared
        """
        count = 0
        for cache_file in self.cache_dir.glob("*.json"):
            try:
                cache_file.unlink()
                count += 1
            except Exception as e:
                logger.warning(f"Failed to delete cache file {cache_file}: {e}")

        logger.info(f"Cleared {count} cache entries")
        return count

    def get_cache_stats(self) -> Dict[str, Any]:
        """
        Get cache statistics

        Returns:
            Dictionary with cache stats
        """
        cache_files = list(self.cache_dir.glob("*.json"))
        total_size = sum(f.stat().st_size for f in cache_files)

        valid_count = 0
        expired_count = 0

        for cache_file in cache_files:
            try:
                with open(cache_file, 'r') as f:
                    cache_data = json.load(f)
                cached_at = datetime.fromisoformat(cache_data['cached_at'])
                if datetime.now() - cached_at > self.ttl:
                    expired_count += 1
                else:
                    valid_count += 1
            except:
                expired_count += 1

        return {
            'total_entries': len(cache_files),
            'valid_entries': valid_count,
            'expired_entries': expired_count,
            'total_size_bytes': total_size,
            'total_size_mb': round(total_size / (1024 * 1024), 2),
            'cache_dir': str(self.cache_dir.absolute()),
        }


# Global cache instance
_cache = None


def get_cache(cache_dir: str = ".mock_data_cache", ttl_hours: int = 24) -> MockDataCache:
    """
    Get or create global cache instance

    Args:
        cache_dir: Directory to store cache files
        ttl_hours: Time-to-live for cache entries in hours

    Returns:
        MockDataCache instance
    """
    global _cache
    if _cache is None:
        _cache = MockDataCache(cache_dir=cache_dir, ttl_hours=ttl_hours)
    return _cache
