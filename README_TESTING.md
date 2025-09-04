# Testing Guide for Virtual BA Workflow

This guide explains how to test the Virtual BA LangGraph workflow using the provided test scripts.

## Test Scripts

### 1. `test_tools_only.py` (Recommended for initial testing)
This script tests individual tools without requiring OpenAI API key or router/decider components.

**Features:**
- Tests all 4 tools individually
- Tests tool chaining (metrics → advisory)
- Tests with different data scenarios (complete, incomplete, empty)
- No external dependencies required

**Usage:**
```bash
python test_tools_only.py
```

### 2. `test_workflow.py` (Full workflow testing)
This script tests the complete workflow including router and decider components.

**Features:**
- Tests individual tools
- Tests router with different user inputs
- Tests decider logic
- Tests graph compilation
- Tests complete workflow execution
- Requires OpenAI API key for router/decider components

**Usage:**
```bash
python test_workflow.py
```

## Dummy Data Structure

The test scripts use a comprehensive dummy process report with the following structure:

```python
{
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
        # ... more steps
    ],
    "stakeholders": [
        {"role": "Customer", "responsibility": "Provide information and documents"},
        # ... more stakeholders
    ],
    "metrics": {
        "target_completion_time": 120,
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
```

## Tool Testing Scenarios

### Query QA Tool
- Tests with various questions about the process
- Verifies responses are generated correctly

### Fill Knowledge Gap Tool
- Tests with complete process data (should find no gaps)
- Tests with incomplete data (should identify missing information)

### Calculate Metrics Tool
- Tests with complete process data
- Tests with empty data
- Verifies metric calculations are correct

### Generate Advisory Tool
- Tests with normal process complexity
- Tests with high complexity process
- Verifies recommendations are generated based on metrics

### Tool Chaining
- Tests metrics calculation followed by advisory generation
- Verifies state is properly passed between tools

## Expected Output

### Tool-Only Tests
```
🚀 Starting Tool-Only Tests
============================================================

🔍 Testing Query QA Tool
========================================
Question: What is the average completion time?
Response: Here's what I found about the process: [stub for: What is the average completion time?]
------------------------------
...

🔍 Testing Fill Knowledge Gap Tool
========================================
Complete data response: The process documentation appears complete. No significant knowledge gaps identified.

Incomplete data response: I've identified the following knowledge gaps:
• Process steps not documented
• Performance metrics not available
• Stakeholder roles not defined
...
```

### Full Workflow Tests
```
🚀 Starting Virtual BA Workflow Tests
============================================================

🧪 Testing Individual Tools...
==================================================
1. Testing Query QA Tool:
Response: Here's what I found about the process: [stub for: What is the average completion time?]

2. Testing Fill Knowledge Gap Tool:
Response: The process documentation appears complete. No significant knowledge gaps identified.
...
```

## Troubleshooting

### Common Issues

1. **Import Errors**: Make sure you're running the script from the project root directory
2. **OpenAI API Key Missing**: Router and decider tests will fail without API key - this is expected
3. **Module Not Found**: Ensure all tool files are in the correct locations

### Environment Setup

1. Install dependencies:
```bash
pip install langgraph langchain-openai
```

2. Set OpenAI API key (for full workflow testing):
```bash
export OPENAI_API_KEY="your-api-key-here"
```

3. Run tests:
```bash
# Start with tool-only tests
python test_tools_only.py

# Then try full workflow tests
python test_workflow.py
```

## Customizing Tests

You can modify the dummy data in the test scripts to test different scenarios:

1. **Different Process Types**: Modify `create_dummy_process_report()` function
2. **Edge Cases**: Add tests with empty or malformed data
3. **Performance Testing**: Add larger datasets
4. **Integration Testing**: Test with real process data

## Next Steps

After running the tests successfully:

1. Review the tool outputs to ensure they meet your requirements
2. Modify tool logic based on test results
3. Add more specific test cases for your use cases
4. Integrate with real process data sources 