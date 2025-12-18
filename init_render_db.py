"""
Render initialization script - runs after database is ready
"""
import asyncio
import sys


async def init_database():
    """Initialize database tables on Render."""
    print("Initializing database tables...")
    
    try:
        from backend.database import init_db
        await init_db()
        print("✓ Database initialized successfully!")
        return 0
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        return 1


if __name__ == "__main__":
    exit_code = asyncio.run(init_database())
    sys.exit(exit_code)
