#!/usr/bin/env python3
"""Tests for ProcessRepository CRUD operations."""

import asyncio

import pytest
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import sessionmaker

from app.db.base import Base
from app.models.user import User
from app.repositories.process import ProcessRepository


# Test database setup
@pytest.fixture
async def engine():
    """Create test database engine."""
    from app.db.session import engine

    async with engine.begin() as conn:
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
    user1 = User(gpn="user1", email="user1@test.com", display_name="Test User 1")
    user2 = User(gpn="user2", email="user2@test.com", display_name="Test User 2")

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

    async def test_get_nonexistent_process(self, process_repo, session):
        """Test retrieving a non-existent process."""
        process = await process_repo.get(999)
        assert process is None

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

    async def test_get_by_nonexistent_mod_guid(self, process_repo, session):
        """Test retrieving a process by non-existent mod_guid."""
        process = await process_repo.get_by_mod_guid("nonexistent-guid")
        assert process is None

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

    async def test_update_nonexistent_process(self, process_repo, session):
        """Test updating a non-existent process."""
        updated_process = await process_repo.update(999, name="Updated Name")
        assert updated_process is None

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


# Run tests
if __name__ == "__main__":
    # Simple test runner for manual testing
    async def run_tests():
        """Run tests manually."""
        from app.db.session import engine

        async_session = sessionmaker(
            engine, class_=AsyncSession, expire_on_commit=False
        )
        async with async_session() as session:
            # Create test users first
            user1 = User(
                gpn="user1", email="user1@test.com", display_name="Test User 1"
            )
            user2 = User(
                gpn="user2", email="user2@test.com", display_name="Test User 2"
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

            # Test delete
            print("6. Testing delete...")
            await repo.delete(process.id)
            deleted = await repo.get(process.id)
            print(f"   ✅ Deleted process: {deleted is None}")

            print("🎉 All tests passed!")

    asyncio.run(run_tests())
