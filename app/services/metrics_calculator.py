from __future__ import annotations

from typing import Dict, List, Set

MANUAL_TASK_TYPES = {"manual task", "user task"}

class BPMNMetricsCalculator:
    """Calculate simple metrics for a BPMN-like process description.

    The calculator expects a dictionary with a ``steps`` key containing a list
    of step dictionaries. Each step should contain ``name``, ``type`` and
    optional ``previous_steps``/``next_steps`` lists referencing other steps by
    name.
    """

    def __init__(self, process: Dict):
        self.process = process
        self.steps: List[Dict] = process.get("steps", [])
        self._step_by_name: Dict[str, Dict] = {s["name"]: s for s in self.steps}

    # ------------------------------------------------------------------
    # basic metrics
    def total_steps(self) -> int:
        """Return the number of steps in the process."""
        return len(self.steps)

    def manual_task_percentage(self) -> float:
        """Return percentage of manual tasks among all task steps."""
        tasks = [s for s in self.steps if "task" in s.get("type", "").lower()]
        if not tasks:
            return 0.0
        manual = [
            s for s in tasks if s.get("type", "").lower() in MANUAL_TASK_TYPES
        ]
        return (len(manual) / len(tasks)) * 100

    def pathway_count(self) -> int:
        """Return number of distinct paths from start to end.

        A start step is any step without ``previous_steps``. A path ends when a
        step has no ``next_steps``. Cycles are ignored by tracking the visited
        nodes in the current traversal.
        """

        def dfs(name: str, visited: Set[str]) -> int:
            step = self._step_by_name.get(name)
            if not step:
                return 0
            next_steps = step.get("next_steps", [])
            if not next_steps:
                return 1
            paths = 0
            for nxt in next_steps:
                if nxt in visited:
                    continue  # break cycles
                paths += dfs(nxt, visited | {nxt})
            return paths

        start_steps = [s for s in self.steps if not s.get("previous_steps")]
        return sum(dfs(s["name"], {s["name"]}) for s in start_steps)

    def all_metrics(self) -> Dict[str, float]:
        """Compute a dictionary of common metrics."""
        return {
            "total_steps": self.total_steps(),
            "manual_task_percentage": self.manual_task_percentage(),
            "pathway_count": self.pathway_count(),
        }


def calculate_metrics(process: Dict) -> Dict[str, float]:
    """Convenience function returning all metrics for ``process``."""
    return BPMNMetricsCalculator(process).all_metrics()
