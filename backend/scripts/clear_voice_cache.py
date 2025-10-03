"""
Script to clear voice cache from Redis
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from app.services.database.redis_service import RedisService


async def clear_voice_cache():
    """Clear all voice cache entries from Redis"""
    print("🗑️  Clearing voice cache from Redis...")
    
    # Initialize Redis service
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379/0')
    redis_service = RedisService(redis_url)
    
    try:
        # Connect to Redis
        await redis_service.connect()
        print(f"🔗 Connected to Redis: {redis_url}")
        
        # Get all voice cache keys
        voice_keys = await redis_service.redis.keys("voice:*")
        print(f"📋 Found {len(voice_keys)} voice cache entries")
        
        if voice_keys:
            # Delete all voice cache keys
            deleted_count = await redis_service.redis.delete(*voice_keys)
            print(f"✅ Deleted {deleted_count} voice cache entries")
        else:
            print("ℹ️  No voice cache entries found")
            
    except Exception as e:
        print(f"❌ Error clearing voice cache: {e}")
        raise
    finally:
        # Close Redis connection
        await redis_service.close()
        print("🔌 Redis connection closed")


async def main():
    """Main function to clear voice cache"""
    print("🚀 Starting voice cache clear...")
    await clear_voice_cache()
    print("\n🎉 Voice cache cleared successfully!")
    print("📊 Next session creation will generate fresh audio files")


if __name__ == "__main__":
    asyncio.run(main())
