#!/usr/bin/env python3
"""Quick test script to verify API flow for processes, projects, reports and metrics."""

import asyncio
import uuid

import httpx
import pytest
from httpx import ASGITransport

from app.core.log import logger
from app.db.base import Base
from app.db.session import AsyncSessionMaker, engine
from app.main import app
from app.repositories.metrics import MetricDefRepository, MetricValueRepository


@pytest.mark.asyncio
async def test_apis() -> None:
    """Exercise the API endpoints including metrics and reports."""
    # Reset database state so tests can be rerun without unique constraint errors
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    transport = ASGITransport(app=app)

    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        # Create a user

        user_data = {
            "gpn": f"test-user-{uuid.uuid4().hex}",
            "email": "test@example.com",
            "display_name": "Test User",
        }
        resp = await client.post("/api/v1/users/", json=user_data)
        logger.info(f"Response: {resp.json()}, code: {resp.status_code}")
        assert resp.status_code == 201
        user_id = resp.json()["id"]

        # Create a process
        process_data = {
            "name": "Test Process",
            "description": "A test process for API testing",
            "mod_guid": "test-guid-456",
            "owner_id": user_id,
            "is_public": True,
        }
        resp = await client.post("/api/v1/processes/", json=process_data)
        logger.info(f"Response: {resp.json()}, code: {resp.status_code}")
        assert resp.status_code == 201
        process_id = resp.json()["id"]

        # Create a project
        project_data = {"name": "Test Project", "description": "Project for API"}
        resp = await client.post(
            f"/api/v1/processes/{process_id}/projects/", json=project_data
        )
        logger.info(f"Response: {resp.json()}, code: {resp.status_code}")
        assert resp.status_code == 201
        project_id = resp.json()["id"]

        # Attach a report
        report_data = {
            "title": "Initial Report",
            "sections": {"overview": {"text": "Initial overview"}},
        }
        resp = await client.post(
            f"/api/v1/processes/{process_id}/projects/{project_id}/reports",
            json=report_data,
        )
        logger.info(f"Response: {resp.json()}, code: {resp.status_code}")
        assert resp.status_code == 201

        # Insert a metric value directly via repository
        async with AsyncSessionMaker() as session:
            metric_def_repo = MetricDefRepository(session)
            metric_val_repo = MetricValueRepository(session)
            metric_def = await metric_def_repo.create(name="accuracy", unit="%")
            await session.commit()
            await metric_val_repo.create(
                metric_id=metric_def.id, process_id=process_id, value_num=0.95
            )
            await session.commit()

        # Retrieve project including reports
        resp = await client.get(
            f"/api/v1/processes/{process_id}/projects/{project_id}",
            params={"include_reports": True},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert len(data["reports"]) == 1

        # List metrics via endpoint
        resp = await client.get(
            f"/api/v1/processes/{process_id}/metrics"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1

        # List reports via endpoint
        resp = await client.get(
            f"/api/v1/processes/{process_id}/projects/{project_id}/reports"
        )
        assert resp.status_code == 200
        assert len(resp.json()) == 1


if __name__ == "__main__":
    asyncio.run(test_apis())
