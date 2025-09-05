import json
import os
from pathlib import Path

import pytest

from app.core.config import settings
from app.workflows import graph

# Skip if the OpenAI client library is not installed
pytest.importorskip("openai")

api_key = settings.openai_api_key

HAS_API_KEY = bool(api_key)

@pytest.mark.skipif(not HAS_API_KEY, reason="no LLM API key configured")
@pytest.mark.parametrize("json_path", Path("test_data").glob("*.json"))
def test_workflow_with_real_llm(json_path):
    """Run the analysis workflow against real LLMs for each BPMN sample."""

    with open(json_path) as f:
        process = json.load(f)

    # Build the LangGraph workflow and execute synchronously
    compiled = graph.build_graph().compile()
    state = {
        "process": process,
        "messages": [{"role": "user", "content": "What are key metrics?"}],
    }
    result = compiled.invoke(state)

    report = result.get("report", {})
    assert set(report.keys()) == {
        "overview",
        "improvements",
        "data_quality",
        "questions",
    }

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    out_file = output_dir / f"{json_path.stem}_live_report.json"
    with open(out_file, "w") as f:
        json.dump(
            {"report": report, "reply": result["messages"][-1].content},
            f,
            indent=2,
        )
