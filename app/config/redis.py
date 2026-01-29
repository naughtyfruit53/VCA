"""
Redis connection management for conversation state.

This module provides Redis connection pooling for managing live call
conversation state. Redis is used ONLY for ephemeral session data.
PostgreSQL remains the source of truth for all persistent data.

Usage:
    from app.config.redis import get_redis_client
    
    redis = await get_redis_client()
    await redis.set(f"call:{call_id}:state", json.dumps(state))
"""

import logging
from typing import Optional
import redis.asyncio as redis

from app.config.settings import settings


logger = logging.getLogger(__name__)


# Global Redis connection pool
_redis_pool: Optional[redis.ConnectionPool] = None
_redis_client: Optional[redis.Redis] = None


async def init_redis() -> None:
    """
    Initialize Redis connection pool.
    
    This should be called once at application startup.
    Creates a connection pool for efficient connection reuse.
    
    Raises:
        redis.ConnectionError: If Redis is not reachable
    """
    global _redis_pool, _redis_client
    
    try:
        logger.info(f"Initializing Redis connection pool: {settings.redis_url}")
        
        # Create connection pool
        _redis_pool = redis.ConnectionPool.from_url(
            settings.redis_url,
            encoding="utf-8",
            decode_responses=True,
            max_connections=10
        )
        
        # Create client from pool
        _redis_client = redis.Redis(connection_pool=_redis_pool)
        
        # Test connection
        await _redis_client.ping()
        
        logger.info("Redis connection pool initialized successfully")
        
    except Exception as e:
        logger.error(f"Failed to initialize Redis: {type(e).__name__}: {e}")
        raise


async def close_redis() -> None:
    """
    Close Redis connection pool.
    
    This should be called once at application shutdown.
    Ensures all connections are properly closed.
    """
    global _redis_pool, _redis_client
    
    try:
        if _redis_client:
            await _redis_client.close()
            logger.info("Redis client closed")
        
        if _redis_pool:
            await _redis_pool.disconnect()
            logger.info("Redis connection pool closed")
            
    except Exception as e:
        logger.error(f"Error closing Redis: {type(e).__name__}: {e}")
    
    finally:
        _redis_pool = None
        _redis_client = None


async def get_redis_client() -> redis.Redis:
    """
    Get Redis client for conversation state management.
    
    Returns a Redis client from the connection pool.
    The pool must be initialized first via init_redis().
    
    Returns:
        redis.Redis: Redis client instance
        
    Raises:
        RuntimeError: If Redis pool is not initialized
    """
    if _redis_client is None:
        raise RuntimeError(
            "Redis pool not initialized. Call init_redis() first."
        )
    
    return _redis_client


# Key naming conventions for Redis
# =================================
# All keys should follow these patterns for consistency:
#
# Call state: "call:{call_id}:state" -> JSON conversation state
# Call turns: "call:{call_id}:turns" -> Integer turn count
# Call started: "call:{call_id}:started_at" -> Unix timestamp
# Call lock: "call:{call_id}:lock" -> Lock for atomic operations
#
# TTL: All call-related keys should expire after call ends + 1 hour
# This prevents memory leaks from abandoned calls.
