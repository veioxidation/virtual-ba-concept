import json
import sys
from pathlib import Path

# Ensure project root on path for imports
sys.path.append(str(Path(__file__).resolve().parents[1]))

from app.services.metrics_calculator import BPMNMetricsCalculator, calculate_metrics


TEST_FILE = Path(__file__).resolve().parents[1] / 'test_data' / 'client_onboarding.json'


def load_process() -> dict:
    with open(TEST_FILE) as f:
        return json.load(f)


def test_calculate_metrics_convenience_function():
    process = load_process()
    metrics = calculate_metrics(process)
    assert metrics == {
        'total_steps': 24,
        'manual_task_percentage': 100.0,
        'pathway_count': 8,
    }


def test_metrics_calculator_methods():
    process = load_process()
    calc = BPMNMetricsCalculator(process)
    assert calc.total_steps() == 24
    assert calc.manual_task_percentage() == 100.0
    assert calc.pathway_count() == 8
