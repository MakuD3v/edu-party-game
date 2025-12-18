"""
Database setup and initialization script.
This script helps configure the database and creates initial tables.
"""
import asyncio
import os
from getpass import getpass


async def setup_database():
    """Interactive database setup."""
    print("=" * 60)
    print("EDU PARTY - Database Setup")
    print("=" * 60)
    print()
    
    # Get database credentials
    print("Please enter your PostgreSQL credentials:")
    print("(Press Enter to use default values shown in brackets)")
    print()
    
    db_host = input("Host [localhost]: ").strip() or "localhost"
    db_port = input("Port [5432]: ").strip() or "5432"
    db_name = input("Database name [eduparty]: ").strip() or "eduparty"
    db_user = input("Username [postgres]: ").strip() or "postgres"
    db_password = getpass("Password: ").strip()
    
    # Construct DATABASE_URL
    database_url = f"postgresql+asyncpg://{db_user}:{db_password}@{db_host}:{db_port}/{db_name}"
    
    print()
    print("Creating .env file...")
    
    # Create .env file
    env_content = f"""# Environment Configuration for EDU Party

# Database Configuration
DATABASE_URL={database_url}

# JWT Secret Key (CHANGE THIS IN PRODUCTION!)
SECRET_KEY=edu-party-secret-key-change-in-production-12345

# CORS Origins
CORS_ORIGINS=*

# Server Configuration
HOST=0.0.0.0
PORT=8000
"""
    
    with open(".env", "w") as f:
        f.write(env_content)
    
    print("✓ .env file created!")
    print()
    
    # Set environment variable temporarily for this session
    os.environ["DATABASE_URL"] = database_url
    
    # Initialize database
    print("Initializing database tables...")
    try:
        from backend.database import init_db
        await init_db()
        print("✓ Database tables created successfully!")
    except Exception as e:
        print(f"✗ Error initializing database: {e}")
        print()
        print("Please make sure:")
        print("  1. PostgreSQL is running")
        print("  2. The database 'eduparty' exists (create it with: createdb eduparty)")
        print("  3. Your credentials are correct")
        return False
    
    print()
    print("=" * 60)
    print("Setup complete! You can now run the server with:")
    print("  python -m uvicorn backend.main:app --reload")
    print("=" * 60)
    return True


if __name__ == "__main__":
    asyncio.run(setup_database())
