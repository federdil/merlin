#!/usr/bin/env python3
"""
Merlin Personal Knowledge Curator - Startup Script
Strands Agents Architecture v2.0
"""

import os
import sys
import uvicorn
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

def main():
    """Start the Merlin API server."""
    print("🧙‍♂️ Starting Merlin Personal Knowledge Curator v2.0")
    print("🏗️  Architecture: Strands Agents")
    print("🚀 API Server: http://127.0.0.1:8002")
    print("📱 Streamlit UI: streamlit run app/streamlit_app.py")
    print("-" * 50)
    
    # Check for required environment variables
    required_env_vars = ["DATABASE_URL", "ANTHROPIC_API_KEY"]
    missing_vars = [var for var in required_env_vars if not os.getenv(var)]
    
    if missing_vars:
        print(f"⚠️  Warning: Missing environment variables: {', '.join(missing_vars)}")
        print("   Please set these in your .env file or environment")
        print()
    
    # Start the FastAPI server
    uvicorn.run(
        "app.main:app",
        host="127.0.0.1",
        port=8002,
        reload=True,
        log_level="info"
    )

if __name__ == "__main__":
    main()
