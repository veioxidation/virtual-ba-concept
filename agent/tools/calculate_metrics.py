from __future__ import annotations

from app.services.metrics_calculator import calculate_metrics as _calculate


def calculate_metrics(state: dict) -> dict:
    """Tool to calculate and analyze basic process metrics."""

    process = state.get("process_report", {})
    metrics = _calculate(process) if process else {}

    if metrics:
        answer = "Here are the calculated process metrics:\n\n" + "\n".join(
            [f"• **{k.replace('_', ' ').title()}**: {v}" for k, v in metrics.items()]
        )
    else:
        answer = (
            "Unable to calculate metrics due to insufficient process data. "
            "Please ensure process steps are available."
        )

    state["conversation_history"] = {"role": "assistant", "content": answer}
    state["calculated_metrics"] = metrics
    return state
