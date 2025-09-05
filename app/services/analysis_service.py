from __future__ import annotations

from sqlalchemy.ext.asyncio import AsyncSession

from app.services.project_service import ProjectService
from app.workflows.state import WorkflowState


class AnalysisService:
    """Service orchestrating the analysis workflow for a project."""

    def __init__(self, graph, session: AsyncSession):
        self.graph = graph
        self.project_service = ProjectService(session)
        self.session = session

    async def generate_project_report(self, project_id: int, process: dict) -> dict:
        """Execute the LangGraph workflow and persist the resulting report."""
        config = {"configurable": {"thread_id": f"project-{project_id}"}}
        state: WorkflowState = {"process": process}
        result = await self.graph.ainvoke(state, config=config)
        report = result.get("report", {})
        await self.project_service.add_report(
            project_id,
            title="Process analysis",
            sections=report,
            thread_id=config["configurable"]["thread_id"],
        )
        return report
