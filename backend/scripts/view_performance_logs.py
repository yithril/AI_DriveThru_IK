"""
Script to view performance logs for debugging
"""

import asyncio
import os
import sys
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables
load_dotenv()

# Add the app directory to the Python path
sys.path.append(str(Path(__file__).parent.parent))

from tortoise import Tortoise
from app.services.database.redis_service import RedisService


async def view_performance_logs():
    """View all performance logs from Redis"""
    print("🔍 Viewing Performance Logs...")
    
    # Initialize Redis
    redis_url = os.getenv('REDIS_URL', 'redis://localhost:6379')
    redis_service = RedisService(redis_url)
    
    try:
        # Get all session keys
        client = await redis_service.get_client()
        session_keys = await client.keys("session:*:performance")
        
        if not session_keys:
            print("❌ No performance logs found")
            return
        
        print(f"📊 Found {len(session_keys)} session performance logs")
        
        for key in session_keys:
            session_id = key.split(':')[1]
            print(f"\n📋 Session: {session_id}")
            print("=" * 50)
            
            # Get performance logs
            logs = await redis_service.get_json(key)
            
            if not logs:
                print("  No performance data")
                continue
            
            # Calculate totals
            total_time = sum(log["duration_ms"] for log in logs)
            step_totals = {}
            
            for log in logs:
                step = log["step_name"]
                duration = log["duration_ms"]
                
                if step not in step_totals:
                    step_totals[step] = {"count": 0, "total_ms": 0}
                
                step_totals[step]["count"] += 1
                step_totals[step]["total_ms"] += duration
            
            # Display summary
            print(f"  Total Processing Time: {total_time:.2f}ms")
            print(f"  Steps Executed: {len(logs)}")
            print()
            
            # Display step breakdown
            print("  Step Breakdown:")
            for step, data in step_totals.items():
                avg_time = data["total_ms"] / data["count"]
                print(f"    {step}: {data['count']} calls, {data['total_ms']:.2f}ms total, {avg_time:.2f}ms avg")
            
            print()
            
            # Display detailed logs
            print("  Detailed Logs:")
            for i, log in enumerate(logs, 1):
                timestamp = log["timestamp"]
                step = log["step_name"]
                duration = log["duration_ms"]
                metadata = log.get("metadata", {})
                
                print(f"    {i}. {timestamp} - {step}: {duration:.2f}ms")
                if metadata:
                    for key, value in metadata.items():
                        print(f"       {key}: {value}")
                print()
    
    except Exception as e:
        print(f"❌ Error viewing performance logs: {e}")
    
    finally:
        # Close Redis connection
        client = await redis_service.get_client()
        await client.aclose()


async def main():
    """Main function"""
    await view_performance_logs()


if __name__ == "__main__":
    asyncio.run(main())
