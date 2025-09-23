#!/usr/bin/env python3
"""Tests for ProcessRepository CRUD operations."""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker
from app.db.base import Base
from app.models.user import User, UserRole
from app.repositories.process import ProcessRepository


# Test database setup
@pytest.fixture
async def engine():
    """Create test database engine."""
    from app.db.session import engine

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)
    yield engine


@pytest.fixture
async def session(engine):
    """Create test database session."""
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)
    async with async_session() as session:
        yield session


@pytest.fixture
async def test_users(session):
    """Create test users."""
    # Create test users
    user1 = User(
        gpn="user1",
        email="user1@test.com",
        display_name="Test User 1",
        azure_oid="00000000-0000-0000-0000-000000000001",
        role=UserRole.PROCESS_CREATOR,
    )
    user2 = User(
        gpn="user2",
        email="user2@test.com",
        display_name="Test User 2",
        azure_oid="00000000-0000-0000-0000-000000000002",
        role=UserRole.VIEWER,
    )

    session.add(user1)
    session.add(user2)
    await session.flush()

    yield [user1, user2]


@pytest.fixture
def process_repo(session):
    """Create ProcessRepository instance."""
    return ProcessRepository(session)


class TestProcessRepository:
    """Test cases for ProcessRepository."""

    @pytest.mark.asyncio
    async def test_create_process(self, process_repo, session, test_users):
        """Test creating a new process."""
        user1 = test_users[0]

        # Create a process
        process = await process_repo.create(
            name="Test Process",
            description="A test process for testing",
            mod_guid="test-guid-123",
            owner_id=user1.id,
            is_public=True,
        )

        # Verify the process was created
        assert process.id is not None
        assert process.name == "Test Process"
        assert process.description == "A test process for testing"
        assert process.mod_guid == "test-guid-123"
        assert process.owner_id == user1.id
        assert process.is_public is True
        assert process.created_at is not None
        assert process.updated_at is not None

    @pytest.mark.asyncio
    async def test_get_process(self, process_repo, session):
        """Test retrieving a process by ID."""
        # Create a process first
        created_process = await process_repo.create(
            name="Test Process", description="A test process"
        )

        # Retrieve the process
        retrieved_process = await process_repo.get(created_process.id)

        # Verify it's the same process
        assert retrieved_process is not None
        assert retrieved_process.id == created_process.id
        assert retrieved_process.name == "Test Process"
        assert retrieved_process.description == "A test process"

    @pytest.mark.asyncio
    async def test_get_nonexistent_process(self, process_repo, session):
        """Test retrieving a non-existent process."""
        process = await process_repo.get(999)
        assert process is None

    @pytest.mark.asyncio
    async def test_get_by_mod_guid(self, process_repo, session):
        """Test retrieving a process by mod_guid."""
        # Create a process with a specific GUID
        created_process = await process_repo.create(
            name="Test Process",
            description="A test process",
            mod_guid="unique-guid-456",
        )

        # Retrieve by GUID
        retrieved_process = await process_repo.get_by_mod_guid("unique-guid-456")

        # Verify it's the same process
        assert retrieved_process is not None
        assert retrieved_process.id == created_process.id
        assert retrieved_process.mod_guid == "unique-guid-456"

    @pytest.mark.asyncio
    async def test_get_by_nonexistent_mod_guid(self, process_repo, session):
        """Test retrieving a process by non-existent mod_guid."""
        process = await process_repo.get_by_mod_guid("nonexistent-guid")
        assert process is None

    @pytest.mark.asyncio
    async def test_update_process(self, process_repo, session):
        """Test updating a process."""
        # Create a process
        process = await process_repo.create(
            name="Original Name", description="Original description", is_public=False
        )

        # Update the process
        updated_process = await process_repo.update(
            process.id,
            name="Updated Name",
            description="Updated description",
            is_public=True,
        )

        # Verify the update
        assert updated_process is not None
        assert updated_process.name == "Updated Name"
        assert updated_process.description == "Updated description"
        assert updated_process.is_public is True

        # Verify the original process is unchanged
        assert process.name == "Original Name"
        assert process.description == "Original description"
        assert process.is_public is False

    @pytest.mark.asyncio
    async def test_update_process_partial(self, process_repo, session):
        """Test updating only some fields of a process."""
        # Create a process
        process = await process_repo.create(
            name="Original Name", description="Original description", is_public=False
        )

        # Update only the name
        updated_process = await process_repo.update(process.id, name="Updated Name")

        # Verify only the name was updated
        assert updated_process is not None
        assert updated_process.name == "Updated Name"
        assert updated_process.description == "Original description"  # Unchanged
        assert updated_process.is_public is False  # Unchanged

    @pytest.mark.asyncio
    async def test_update_nonexistent_process(self, process_repo, session):
        """Test updating a non-existent process."""
        updated_process = await process_repo.update(999, name="Updated Name")
        assert updated_process is None

    @pytest.mark.asyncio
    async def test_delete_process(self, process_repo, session):
        """Test deleting a process."""
        # Create a process
        process = await process_repo.create(
            name="Process to Delete", description="This will be deleted"
        )
        process_id = process.id

        # Verify it exists
        retrieved_process = await process_repo.get(process_id)
        assert retrieved_process is not None

        # Delete the process
        await process_repo.delete(process_id)

        # Verify it's gone
        deleted_process = await process_repo.get(process_id)
        assert deleted_process is None

    @pytest.mark.asyncio
    async def test_list_processes(self, process_repo, session):
        """Test listing processes with pagination."""
        # Create multiple processes
        await process_repo.create(name="Process 1", description="First process")
        await process_repo.create(name="Process 2", description="Second process")
        await process_repo.create(name="Process 3", description="Third process")

        # List all processes
        processes = await process_repo.list()
        assert len(processes) == 3

        # Test pagination
        processes_page1 = await process_repo.list(offset=0, limit=2)
        assert len(processes_page1) == 2

        processes_page2 = await process_repo.list(offset=2, limit=2)
        assert len(processes_page2) == 1

    @pytest.mark.asyncio
    async def test_list_public_processes(self, process_repo, session):
        """Test listing only public processes."""
        # Create public and private processes
        await process_repo.create(name="Public Process 1", is_public=True)
        await process_repo.create(name="Private Process 1", is_public=False)
        await process_repo.create(name="Public Process 2", is_public=True)
        await process_repo.create(name="Private Process 2", is_public=False)

        # List only public processes
        public_processes = await process_repo.list_public()
        assert len(public_processes) == 2

        # Verify all returned processes are public
        for process in public_processes:
            assert process.is_public is True

    @pytest.mark.asyncio
    async def test_list_by_owner(self, process_repo, session, test_users):
        """Test listing processes by owner."""
        user1, user2 = test_users

        # Create processes for different owners
        await process_repo.create(name="User 1 Process 1", owner_id=user1.id)
        await process_repo.create(name="User 1 Process 2", owner_id=user1.id)
        await process_repo.create(name="User 2 Process 1", owner_id=user2.id)
        await process_repo.create(name="User 1 Process 3", owner_id=user1.id)

        # List processes for user 1
        user1_processes = await process_repo.list_by_owner(user1.id)
        assert len(user1_processes) == 3

        # Verify all returned processes belong to user 1
        for process in user1_processes:
            assert process.owner_id == user1.id

        # List processes for user 2
        user2_processes = await process_repo.list_by_owner(user2.id)
        assert len(user2_processes) == 1
        assert user2_processes[0].owner_id == user2.id


from app.repositories.metrics import MetricDefRepository, MetricValueRepository
from app.repositories.project import ProjectRepository
from app.repositories.report import ReportRepository


@pytest.mark.asyncio
async def test_project_report_metric_crud_with_process(
    session, test_users, process_repo
):
    """Test CRUD operations for Project with related Reports and Metrics."""
    user = test_users[0]

    # 1. Create a process
    process = await process_repo.create(
        name="Process for Project",
        description="Process description",
        mod_guid="proc-guid-1",
        owner_id=user.id,
        is_public=True,
    )
    await session.commit()
    assert process.id is not None

    # 2. Create a project linked to the process
    project_repo = ProjectRepository(session)
    project = await project_repo.create(
        name="Test Project",
        description="A project linked to a process",
        process_id=process.id,
    )
    await session.commit()
    assert project.id is not None
    assert project.process_id == process.id

    # 3. Retrieve the project and check linkage
    retrieved = await project_repo.get(project.id)
    assert retrieved is not None
    assert retrieved.name == "Test Project"
    assert retrieved.process_id == process.id

    # 4. Update the project
    updated = await project_repo.update(
        project.id, name="Updated Project Name", description="Updated description"
    )
    await session.commit()
    assert updated is not None
    assert updated.name == "Updated Project Name"
    assert updated.description == "Updated description"

    # 5. Add a report to the project
    report_repo = ReportRepository(session)
    report = await report_repo.create(
        project_id=project.id,
        title="Initial Report",
        sections={"overview": {"text": "Initial overview section"}},
        created_by_id=user.id,
        thread_id="thread-123",
    )
    await session.commit()
    assert report.id is not None
    assert report.project_id == project.id

    # 6. Retrieve and update the report
    retrieved_report = await report_repo.get(report.id)
    assert retrieved_report is not None
    updated_report = await report_repo.update(
        report.id,
        title="Updated Report Title",
        sections={"overview": {"text": "Updated overview"}},
    )
    await session.commit()
    assert updated_report is not None
    assert updated_report.title == "Updated Report Title"

    # 7. Add a metric definition and value
    metric_def_repo = MetricDefRepository(session)
    metric_val_repo = MetricValueRepository(session)
    metric_def = await metric_def_repo.create(name="throughput", unit="tps")
    await session.commit()
    metric_value = await metric_val_repo.create(
        metric_id=metric_def.id, project_id=project.id, value_num=42.0
    )
    await session.commit()
    assert metric_value.project_id == project.id

    # 8. Retrieve project with reports and metrics
    retrieved_full = await project_repo.get(
        project.id, include_reports=True
    )
    assert len(retrieved_full.reports) == 1

    # 9. Delete the metric
    await metric_val_repo.delete(metric_value.id)
    await session.commit()
    metrics_left = await metric_val_repo.list_by_project(project.id)
    assert metrics_left == []

    # 10. Delete the report
    await report_repo.delete(report.id)
    await session.commit()
    deleted_report = await report_repo.get(report.id)
    assert deleted_report is None

    # 11. Delete the project
    await project_repo.delete(project.id)
    await session.commit()
    deleted = await project_repo.get(project.id)
    assert deleted is None


# Run tests
if __name__ == "__main__":
    # Simple test runner for manual testing
    @pytest.mark.asyncio
    async def run_tests():
        """Run tests manually."""
        from app.db.session import engine

        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            # Create test users first
            user1 = User(
                gpn="user1",
                email="user1@test.com",
                display_name="Test User 1",
                azure_oid="00000000-0000-0000-0000-000000000001",
                role=UserRole.PROCESS_CREATOR,
            )
            user2 = User(
                gpn="user2",
                email="user2@test.com",
                display_name="Test User 2",
                azure_oid="00000000-0000-0000-0000-000000000002",
                role=UserRole.VIEWER,
            )

            session.add(user1)
            session.add(user2)
            await session.flush()

            repo = ProcessRepository(session)

            print("🧪 Running ProcessRepository tests...")

            # Test create
            print("1. Testing create...")
            process = await repo.create(
                "Test Process", "A test process", "test-guid", user1.id, True
            )
            print(f"   ✅ Created process: {process.name} (ID: {process.id})")

            # Test get
            print("2. Testing get...")
            retrieved = await repo.get(process.id)
            print(f"   ✅ Retrieved process: {retrieved.name}")

            # Test update
            print("3. Testing update...")
            updated = await repo.update(process.id, name="Updated Process")
            print(f"   ✅ Updated process: {updated.name}")

            # Test list
            print("4. Testing list...")
            processes = await repo.list()
            print(f"   ✅ Listed {len(processes)} processes")

            # Test list by owner
            print("5. Testing list by owner...")
            user_processes = await repo.list_by_owner(user1.id)
            print(f"   ✅ Listed {len(user_processes)} processes for user {user1.gpn}")

            # Test project, report and metric CRUD with process
            print("6. Testing project, report and metric crud with process...")
            await test_project_report_metric_crud_with_process(
                session, [user1, user2], repo
            )

            # Test delete
            print("7. Testing delete...")
            await repo.delete(process.id)
            deleted = await repo.get(process.id)
            print(f"   ✅ Deleted process: {deleted is None}")

            # await session.commit()
            print("🎉 All tests passed!")

    asyncio.run(run_tests())
