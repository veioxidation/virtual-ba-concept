#!/usr/bin/env python3
"""
Testing script for the Virtual BA LangGraph workflow.
This script provides dummy data and tests the complete workflow.
"""

import os
import sys
from typing import Dict, Any

# Add the project root to the path
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

def create_dummy_process_report() -> Dict[str, Any]:
    """Create dummy process report data for testing."""
    return {
        "process_name": "Customer Onboarding Process",
        "process_id": "ONB-001",
        "process_steps": [
            {
                "id": 1,
                "name": "Customer Registration",
                "duration": 15,
                "automation_level": "automated",
                "description": "Customer fills out registration form"
            },
            {
                "id": 2,
                "name": "Document Verification",
                "duration": 45,
                "automation_level": "manual",
                "description": "Staff verifies customer documents"
            },
            {
                "id": 3,
                "name": "Account Setup",
                "duration": 30,
                "automation_level": "automated",
                "description": "System creates customer account"
            },
            {
                "id": 4,
                "name": "Welcome Call",
                "duration": 20,
                "automation_level": "manual",
                "description": "Customer service calls new customer"
            },
            {
                "id": 5,
                "name": "First Transaction",
                "duration": 10,
                "automation_level": "automated",
                "description": "Customer makes first transaction"
            }
        ],
        "stakeholders": [
            {"role": "Customer", "responsibility": "Provide information and documents"},
            {"role": "Customer Service", "responsibility": "Verify documents and make welcome call"},
            {"role": "System Admin", "responsibility": "Monitor account creation"}
        ],
        "metrics": {
            "target_completion_time": 120,  # minutes
            "target_success_rate": 0.95,
            "current_success_rate": 0.92
        },
        "historical_data": {
            "completion_times": [110, 125, 95, 130, 115, 100, 140, 105, 120, 135],
            "success_rates": [0.94, 0.91, 0.96, 0.89, 0.93, 0.95, 0.88, 0.94, 0.92, 0.90]
        },
        "current_issues": [
            "Document verification step takes too long",
            "Some customers drop off during welcome call",
            "System occasionally fails during account setup"
        ]
    }

def create_test_state(user_input: str, process_report: Dict[str, Any]):
    """Create a test state with user input and process report."""
    from agent.state_schema import VirtualBAState
    
    return VirtualBAState(
        user_input=user_input,
        process_report=process_report,
        conversation_history=[
            {"role": "user", "content": user_input}
        ],
        route=None,  # Will be set by router
        calculated_metrics={},
        advisory_recommendations=[]
    )

def test_individual_tools():
    """Test individual tools with dummy data."""
    print("🧪 Testing Individual Tools...")
    print("=" * 50)
    
    # Import tools
    from agent.tools.query_qa import query_qa
    from agent.tools.fill_knowledge_gap import fill_knowledge_gap
    from agent.tools.calculate_metrics import calculate_metrics
    from agent.tools.generate_advisory import generate_advisory
    
    # Create dummy data
    process_report = create_dummy_process_report()
    
    # Test 1: Query QA
    print("\n1. Testing Query QA Tool:")
    state = create_test_state("What is the average completion time?", process_report)
    result = query_qa(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
    else:
        response = result['conversation_history'][-1]['content']
    print(f"Response: {response}")
    
    # Test 2: Fill Knowledge Gap
    print("\n2. Testing Fill Knowledge Gap Tool:")
    state = create_test_state("Are there any gaps in our process documentation?", process_report)
    result = fill_knowledge_gap(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
    else:
        response = result['conversation_history'][-1]['content']
    print(f"Response: {response}")
    
    # Test 3: Calculate Metrics
    print("\n3. Testing Calculate Metrics Tool:")
    state = create_test_state("Calculate process metrics", process_report)
    result = calculate_metrics(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
        metrics = result.calculated_metrics
    else:
        response = result['conversation_history'][-1]['content']
        metrics = result.get('calculated_metrics', {})
    print(f"Response: {response}")
    print(f"Calculated metrics: {metrics}")
    
    # Test 4: Generate Advisory
    print("\n4. Testing Generate Advisory Tool:")
    # First calculate metrics, then generate advisory
    state = create_test_state("Generate advisory recommendations", process_report)
    state = calculate_metrics(state)  # Calculate metrics first
    result = generate_advisory(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
        recommendations = result.advisory_recommendations
    else:
        response = result['conversation_history'][-1]['content']
        recommendations = result.get('advisory_recommendations', [])
    print(f"Response: {response}")
    print(f"Recommendations: {recommendations}")

def test_router():
    """Test the router with different user inputs."""
    print("\n🧪 Testing Router...")
    print("=" * 50)
    
    try:
        from agent.router import route_user_input
        
        test_inputs = [
            "What is the average completion time?",
            "Are there any gaps in our process?",
            "Calculate metrics for our process",
            "Give me advisory recommendations",
            "How can we improve efficiency?"
        ]
        
        process_report = create_dummy_process_report()
        
        for user_input in test_inputs:
            state = create_test_state(user_input, process_report)
            result = route_user_input(state)
            print(f"Input: '{user_input}'")
            
            # Handle both object and dict returns
            if hasattr(result, 'route'):
                route = result.route
            else:
                route = result.get('route', 'unknown')
            print(f"Route: {route}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Router test failed (likely due to missing API key): {e}")

def test_decider():
    """Test the decider with different states."""
    print("\n🧪 Testing Decider...")
    print("=" * 50)
    
    try:
        from agent.decider import decide_next_tool
        
        process_report = create_dummy_process_report()
        
        # Test different scenarios
        scenarios = [
            ("query", "User asked a question"),
            ("fill_gap", "Knowledge gap identified"),
            ("metrics", "Metrics calculation requested"),
            ("advisory", "Advisory needed"),
            ("finish", "Task completed")
        ]
        
        for route, description in scenarios:
            state = create_test_state("Test input", process_report)
            # Set route on the state object
            state.route = route
            result = decide_next_tool(state)
            print(f"Scenario: {description}")
            
            # Handle both object and dict returns
            if hasattr(result, 'route'):
                result_route = result.route
            else:
                result_route = result.get('route', 'unknown')
            print(f"Route: {result_route}")
            print("-" * 30)
            
    except Exception as e:
        print(f"Decider test failed: {e}")

def test_graph_compilation():
    """Test that the graph can be compiled successfully."""
    print("\n🧪 Testing Graph Compilation...")
    print("=" * 50)
    
    try:
        from agent.langgraph_runner import build_graph
        
        graph = build_graph()
        print("✅ Graph compiled successfully!")
        print(f"Graph type: {type(graph)}")
        
        # Print graph structure
        print("\nGraph structure:")
        print(f"Nodes: {list(graph.nodes.keys())}")
        
    except Exception as e:
        print(f"❌ Graph compilation failed: {e}")
        import traceback
        traceback.print_exc()

def test_workflow_execution():
    """Test the complete workflow execution."""
    print("\n🧪 Testing Complete Workflow...")
    print("=" * 50)
    
    try:
        from agent.langgraph_runner import build_graph
        
        graph = build_graph()
        process_report = create_dummy_process_report()
        
        # Test different user inputs
        test_cases = [
            "What is the average completion time for our onboarding process?",
            "Calculate all metrics for our process",
            "What are the knowledge gaps in our process?",
            "Give me advisory recommendations for improvement"
        ]
        
        for user_input in test_cases:
            print(f"\nTesting: '{user_input}'")
            print("-" * 40)
            
            initial_state = create_test_state(user_input, process_report)
            
            try:
                # Execute the workflow
                result = graph.invoke(initial_state)
                
                # Print conversation history
                if hasattr(result, 'conversation_history'):
                    conversation = result.conversation_history
                else:
                    conversation = result.get("conversation_history", [])
                
                for message in conversation:
                    role = message.get("role", "unknown")
                    content = message.get("content", "")
                    print(f"{role.upper()}: {content[:100]}{'...' if len(content) > 100 else ''}")
                    
            except Exception as e:
                print(f"Workflow execution failed: {e}")
                
    except Exception as e:
        print(f"Workflow test failed: {e}")

def main():
    """Run all tests."""
    print("🚀 Starting Virtual BA Workflow Tests")
    print("=" * 60)
    
    # Test individual components
    test_individual_tools()
    test_router()
    test_decider()
    test_graph_compilation()
    test_workflow_execution()
    
    print("\n✅ All tests completed!")
    print("\nNote: Some tests may fail if OpenAI API key is not configured.")
    print("This is expected for router and workflow execution tests.")

if __name__ == "__main__":
    main() 