#!/usr/bin/env python3
"""
Test script for Merlin v2.0 Strands Agents architecture
"""

import requests
import json
import time
from typing import Dict, Any

API_URL = "http://127.0.0.1:8002/api/v1"

def test_api_health():
    """Test if the API is running."""
    try:
        response = requests.get("http://127.0.0.1:8002/health", timeout=5)
        if response.status_code == 200:
            print("✅ API Health Check: PASSED")
            return True
        else:
            print(f"❌ API Health Check: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ API Health Check: FAILED (Error: {e})")
        return False

def test_agents_info():
    """Test agents info endpoint."""
    try:
        response = requests.get(f"{API_URL}/agents/info", timeout=10)
        if response.status_code == 200:
            agents_info = response.json()
            print("✅ Agents Info: PASSED")
            print(f"   Available agents: {list(agents_info.keys())}")
            return True
        else:
            print(f"❌ Agents Info: FAILED (Status: {response.status_code})")
            return False
    except Exception as e:
        print(f"❌ Agents Info: FAILED (Error: {e})")
        return False

def test_agent_processing(input_text: str, expected_agent: str = None) -> Dict[str, Any]:
    """Test agent processing with given input."""
    try:
        response = requests.post(
            f"{API_URL}/process",
            json={"input_text": input_text},
            timeout=30
        )
        if response.status_code == 200:
            result = response.json()
            agent_type = result.get("agent_type", "unknown")
            success = result.get("success", False)
            
            if expected_agent and agent_type != expected_agent:
                print(f"⚠️  Expected agent '{expected_agent}', got '{agent_type}'")
            
            if success:
                print(f"✅ Processing: PASSED (Agent: {agent_type})")
                return result
            else:
                print(f"❌ Processing: FAILED (Agent: {agent_type}, Error: {result.get('error')})")
                return result
        else:
            print(f"❌ Processing: FAILED (Status: {response.status_code})")
            return {}
    except Exception as e:
        print(f"❌ Processing: FAILED (Error: {e})")
        return {}

def run_tests():
    """Run all tests."""
    print("🧙‍♂️ Testing Merlin v2.0 Strands Agents Architecture")
    print("=" * 60)
    
    # Test 1: API Health
    if not test_api_health():
        print("\n❌ Cannot proceed - API is not running")
        print("   Please start the API server with: python start_merlin.py")
        return
    
    print()
    
    # Test 2: Agents Info
    test_agents_info()
    print()
    
    # Test 3: Agent Processing Tests
    test_cases = [
        {
            "input": "https://news.ycombinator.com",
            "expected_agent": "ingestion",
            "description": "URL Processing"
        },
        {
            "input": "What are my notes about AI?",
            "expected_agent": "query", 
            "description": "Search Query"
        },
        {
            "input": "This is a test article about machine learning and artificial intelligence...",
            "expected_agent": "ingestion",
            "description": "Text Ingestion"
        },
        {
            "input": "Summarize this: Machine learning is a subset of artificial intelligence...",
            "expected_agent": "summarization",
            "description": "Summarization Request"
        },
        {
            "input": "",
            "expected_agent": "query",
            "description": "Empty Input"
        }
    ]
    
    print("🧪 Testing Agent Processing:")
    print("-" * 40)
    
    for i, test_case in enumerate(test_cases, 1):
        print(f"\nTest {i}: {test_case['description']}")
        print(f"Input: '{test_case['input'][:50]}{'...' if len(test_case['input']) > 50 else ''}'")
        
        result = test_agent_processing(
            test_case['input'], 
            test_case['expected_agent']
        )
        
        if result.get("success"):
            agent_result = result.get("result", {})
            if "note" in agent_result:
                note = agent_result["note"]
                print(f"   → Created note: {note.get('title', 'Untitled')}")
            elif "results" in agent_result:
                results = agent_result["results"]
                print(f"   → Found {len(results)} results")
            elif "generated_summary" in agent_result:
                summary = agent_result["generated_summary"]
                print(f"   → Generated summary: {summary[:100]}{'...' if len(summary) > 100 else ''}")
    
    print("\n" + "=" * 60)
    print("🎉 Test suite completed!")
    print("\nTo start the full system:")
    print("   API: python start_merlin.py")
    print("   UI:  streamlit run app/streamlit_app.py")

if __name__ == "__main__":
    run_tests()
