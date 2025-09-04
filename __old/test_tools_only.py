#!/usr/bin/env python3
"""
Simple test script for individual tools only.
This script tests the tools without requiring router/decider components.
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
        calculated_metrics={},
        advisory_recommendations=[]
    )

def test_query_qa():
    """Test the query_qa tool."""
    print("🔍 Testing Query QA Tool")
    print("=" * 40)
    
    from agent.tools.query_qa import query_qa
    
    process_report = create_dummy_process_report()
    
    test_questions = [
        "What is the average completion time?",
        "How many steps are in the process?",
        "What are the current issues?",
        "Who are the stakeholders?"
    ]
    
    for question in test_questions:
        print(f"\nQuestion: {question}")
        state = create_test_state(question, process_report)
        result = query_qa(state)
        
        # Handle both object and dict returns
        if hasattr(result, 'conversation_history'):
            response = result.conversation_history[-1]['content']
        else:
            response = result['conversation_history'][-1]['content']
        print(f"Response: {response}")
        print("-" * 30)

def test_fill_knowledge_gap():
    """Test the fill_knowledge_gap tool."""
    print("\n🔍 Testing Fill Knowledge Gap Tool")
    print("=" * 40)
    
    from agent.tools.fill_knowledge_gap import fill_knowledge_gap
    
    # Test with complete data
    process_report = create_dummy_process_report()
    state = create_test_state("Are there any gaps?", process_report)
    result = fill_knowledge_gap(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
    else:
        response = result['conversation_history'][-1]['content']
    print(f"Complete data response: {response}")
    
    # Test with incomplete data
    incomplete_report = {
        "process_name": "Incomplete Process",
        "process_id": "INC-001"
        # Missing process_steps, stakeholders, metrics
    }
    state = create_test_state("Are there any gaps?", incomplete_report)
    result = fill_knowledge_gap(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
    else:
        response = result['conversation_history'][-1]['content']
    print(f"\nIncomplete data response: {response}")

def test_calculate_metrics():
    """Test the calculate_metrics tool."""
    print("\n🔍 Testing Calculate Metrics Tool")
    print("=" * 40)
    
    from agent.tools.calculate_metrics import calculate_metrics
    
    process_report = create_dummy_process_report()
    state = create_test_state("Calculate metrics", process_report)
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
    
    # Test with empty data
    empty_report = {"process_name": "Empty Process"}
    state = create_test_state("Calculate metrics", empty_report)
    result = calculate_metrics(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
    else:
        response = result['conversation_history'][-1]['content']
    print(f"\nEmpty data response: {response}")

def test_generate_advisory():
    """Test the generate_advisory tool."""
    print("\n🔍 Testing Generate Advisory Tool")
    print("=" * 40)
    
    from agent.tools.generate_advisory import generate_advisory
    from agent.tools.calculate_metrics import calculate_metrics
    
    process_report = create_dummy_process_report()
    
    # First calculate metrics, then generate advisory
    state = create_test_state("Generate advisory", process_report)
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
    
    # Test with different process data (more complex process)
    complex_report = create_dummy_process_report()
    complex_report["process_steps"].extend([
        {
            "id": 6,
            "name": "Additional Step 1",
            "duration": 60,
            "automation_level": "manual",
            "description": "Very long manual step"
        },
        {
            "id": 7,
            "name": "Additional Step 2",
            "duration": 25,
            "automation_level": "manual",
            "description": "Another manual step"
        }
    ])
    
    state = create_test_state("Generate advisory for complex process", complex_report)
    state = calculate_metrics(state)
    result = generate_advisory(state)
    
    # Handle both object and dict returns
    if hasattr(result, 'conversation_history'):
        response = result.conversation_history[-1]['content']
        recommendations = result.advisory_recommendations
    else:
        response = result['conversation_history'][-1]['content']
        recommendations = result.get('advisory_recommendations', [])
    
    print(f"\nComplex process response: {response}")
    print(f"Complex process recommendations: {recommendations}")

def test_tool_chaining():
    """Test chaining multiple tools together."""
    print("\n🔍 Testing Tool Chaining")
    print("=" * 40)
    
    from agent.tools.calculate_metrics import calculate_metrics
    from agent.tools.generate_advisory import generate_advisory
    
    process_report = create_dummy_process_report()
    state = create_test_state("Analyze our process", process_report)
    
    print("Step 1: Calculate metrics")
    state = calculate_metrics(state)
    
    # Handle both object and dict returns
    if hasattr(state, 'calculated_metrics'):
        metrics = state.calculated_metrics
    else:
        metrics = state.get('calculated_metrics', {})
    print(f"Metrics calculated: {list(metrics.keys())}")
    
    print("\nStep 2: Generate advisory based on metrics")
    state = generate_advisory(state)
    
    # Handle both object and dict returns
    if hasattr(state, 'advisory_recommendations'):
        recommendations = state.advisory_recommendations
    else:
        recommendations = state.get('advisory_recommendations', [])
    print(f"Recommendations generated: {len(recommendations)}")
    
    print("\nFinal conversation:")
    if hasattr(state, 'conversation_history'):
        conversation = state.conversation_history
    else:
        conversation = state.get('conversation_history', [])
    
    for i, message in enumerate(conversation):
        role = message.get('role', 'unknown')
        content = message.get('content', '')
        print(f"{i+1}. {role.upper()}: {content[:80]}{'...' if len(content) > 80 else ''}")

def main():
    """Run all tool tests."""
    print("🚀 Starting Tool-Only Tests")
    print("=" * 60)
    
    test_query_qa()
    test_fill_knowledge_gap()
    test_calculate_metrics()
    test_generate_advisory()
    test_tool_chaining()
    
    print("\n✅ All tool tests completed!")
    print("\nThese tests don't require OpenAI API key and test the core functionality.")

if __name__ == "__main__":
    main() 