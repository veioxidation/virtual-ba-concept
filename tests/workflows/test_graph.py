import json
from pathlib import Path
from types import SimpleNamespace

import pytest

from app.workflows import graph


class DummyResp(SimpleNamespace):
    pass


def test_generate_report_node_parses_model_output(monkeypatch):
    """The node should parse JSON from the LLM into a report dict."""

    def fake_chat_model():
        class Model:
            def invoke(self, messages):  # noqa: D401
                return DummyResp(
                    content=json.dumps(
                        {
                            "overview": "x",
                            "improvements": "y",
                            "data_quality": "z",
                            "questions": "q",
                        }
                    )
                )

        return Model()

    monkeypatch.setattr(graph, "chat_model", fake_chat_model)
    state = {"process": {"name": "demo"}}
    result = graph.generate_report_node(state)
    assert set(result["report"].keys()) == {
        "overview",
        "improvements",
        "data_quality",
        "questions",
    }


@pytest.mark.parametrize("json_path", Path("test_data").glob("*.json"))
def test_generate_report_outputs(json_path, monkeypatch):
    """Generate reports for each BPMN sample and save JSON for review."""

    with open(json_path) as f:
        process = json.load(f)

    def fake_chat_model_factory(name, step_count):
        def _fake_chat_model():
            class Model:
                def invoke(self, messages):  # noqa: D401
                    sections = {
                        "overview": f"{name} has {step_count} steps.",
                        "improvements": "N/A",
                        "data_quality": "N/A",
                        "questions": "N/A",
                    }
                    return DummyResp(content=json.dumps(sections))

            return Model()

        return _fake_chat_model

    monkeypatch.setattr(
        graph,
        "chat_model",
        fake_chat_model_factory(
            process.get("process_name", "Process"), len(process.get("steps", []))
        ),
    )

    state = {"process": process}
    result = graph.generate_report_node(state)
    report = result["report"]
    assert set(report.keys()) == {
        "overview",
        "improvements",
        "data_quality",
        "questions",
    }

    output_dir = Path(__file__).parent / "output"
    output_dir.mkdir(exist_ok=True)
    out_file = output_dir / f"{json_path.stem}_report.json"
    with open(out_file, "w") as f:
        json.dump(report, f, indent=2)
