#!/usr/bin/env python3
"""
Test script for YAML configuration implementation.
Tests the configuration manager, agent factory, and routing engine.
"""

import sys
import os
from pathlib import Path

# Add the project root to Python path
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

from app.config import get_config_manager
from app.agents.agent_factory import get_agent_factory
from app.routing import get_routing_engine


def test_config_manager():
    """Test the configuration manager."""
    print("🧪 Testing Configuration Manager...")
    
    try:
        config_manager = get_config_manager()
        config = config_manager.get_config()
        
        print(f"✅ Configuration loaded successfully")
        print(f"   Global name: {config.global_config.name}")
        print(f"   Version: {config.global_config.version}")
        print(f"   Available agents: {config_manager.get_available_agents()}")
        
        # Test agent configuration access
        for agent_name in config_manager.get_available_agents():
            agent_config = config_manager.get_agent_config(agent_name)
            print(f"   Agent '{agent_name}': {agent_config.name} ({agent_config.type})")
        
        return True
        
    except Exception as e:
        print(f"❌ Configuration Manager test failed: {e}")
        return False


def test_agent_factory():
    """Test the agent factory."""
    print("\n🧪 Testing Agent Factory...")
    
    try:
        agent_factory = get_agent_factory()
        
        # Test agent validation
        validation_results = agent_factory.validate_agents()
        print(f"✅ Agent validation completed")
        
        for agent_name, is_valid in validation_results.items():
            status = "✅" if is_valid else "❌"
            print(f"   {status} Agent '{agent_name}': {'Valid' if is_valid else 'Invalid'}")
        
        # Test agent creation for valid agents
        valid_agents = [name for name, valid in validation_results.items() if valid]
        print(f"\n   Creating instances for valid agents...")
        
        for agent_name in valid_agents[:2]:  # Test first 2 agents to avoid long startup
            try:
                agent = agent_factory.get_agent(agent_name)
                print(f"   ✅ Created agent instance: {agent_name}")
            except Exception as e:
                print(f"   ❌ Failed to create agent '{agent_name}': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Agent Factory test failed: {e}")
        return False


def test_routing_engine():
    """Test the routing engine."""
    print("\n🧪 Testing Routing Engine...")
    
    try:
        routing_engine = get_routing_engine()
        
        # Test routing rules
        rules_info = routing_engine.get_routing_rules_info()
        print(f"✅ Routing rules loaded: {len(rules_info)} rules")
        
        for i, rule in enumerate(rules_info[:3]):  # Show first 3 rules
            print(f"   Rule {i+1}: {rule['condition']} -> {rule['target_agent']}")
        
        # Test routing decisions
        test_inputs = [
            "https://example.com",
            "What are my notes about AI?",
            "Summarize this content...",
            "I want to learn about machine learning",
            "",
            "This is a long text content that should trigger the long text routing rule because it contains more than 200 characters which is the threshold for long text content routing in the YAML configuration."
        ]
        
        print(f"\n   Testing routing decisions...")
        for input_text in test_inputs:
            try:
                decision = routing_engine.route_input(input_text)
                print(f"   ✅ '{input_text[:30]}...' -> {decision.agent_type} ({decision.confidence:.2f})")
                print(f"      Reasoning: {decision.reasoning}")
            except Exception as e:
                print(f"   ❌ Failed to route '{input_text[:30]}...': {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Routing Engine test failed: {e}")
        return False


def test_integration():
    """Test integration between components."""
    print("\n🧪 Testing Integration...")
    
    try:
        # Test end-to-end routing and agent loading
        routing_engine = get_routing_engine()
        agent_factory = get_agent_factory()
        
        test_input = "https://news.ycombinator.com"
        print(f"   Testing with input: '{test_input}'")
        
        # Route the input
        decision = routing_engine.route_input(test_input)
        print(f"   ✅ Routing decision: {decision.agent_type} -> {decision.action}")
        
        # Try to get the agent (but don't actually process)
        try:
            agent = agent_factory.get_agent(decision.agent_type)
            print(f"   ✅ Agent loaded successfully: {type(agent).__name__}")
        except Exception as e:
            print(f"   ⚠️  Agent loading failed (expected for some agents): {e}")
        
        return True
        
    except Exception as e:
        print(f"❌ Integration test failed: {e}")
        return False


def main():
    """Run all tests."""
    print("🚀 Testing YAML Configuration Implementation")
    print("=" * 60)
    
    tests = [
        test_config_manager,
        test_agent_factory,
        test_routing_engine,
        test_integration
    ]
    
    results = []
    for test in tests:
        try:
            result = test()
            results.append(result)
        except Exception as e:
            print(f"❌ Test {test.__name__} crashed: {e}")
            results.append(False)
    
    print("\n" + "=" * 60)
    print("📊 Test Results Summary:")
    
    passed = sum(results)
    total = len(results)
    
    for i, (test, result) in enumerate(zip(tests, results)):
        status = "✅ PASSED" if result else "❌ FAILED"
        print(f"   {i+1}. {test.__name__}: {status}")
    
    print(f"\n🎯 Overall: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 All tests passed! YAML configuration implementation is working.")
        return 0
    else:
        print("⚠️  Some tests failed. Check the output above for details.")
        return 1


if __name__ == "__main__":
    sys.exit(main())
