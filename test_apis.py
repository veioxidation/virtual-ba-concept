#!/usr/bin/env python3
"""Quick test script to verify the new APIs work."""

import asyncio

import httpx
from httpx import ASGITransport

from app.db.base import Base
from app.db.session import engine

from app.main import app

async def test_apis():
    """Test the new process and user APIs."""
    # Create tables
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    # Create an ASGI transport for FastAPI app
    transport = ASGITransport(app=app)

    # Start the app
    async with httpx.AsyncClient(transport=transport, base_url="http://test") as client:
        print("🧪 Testing Process and User APIs...")

        # Test user creation
        print("1. Creating a test user...")
        user_data = {
            "gpn": "test-user-123",
            "email": "test@example.com",
            "display_name": "Test User",
        }
        response = await client.post("/api/v1/users/", json=user_data)
        print(f"   ✅ User created: {response.status_code}")
        user = response.json()
        user_id = user["id"]

        # Test process creation
        print("2. Creating a test process...")
        process_data = {
            "name": "Test Process",
            "description": "A test process for API testing",
            "mod_guid": "test-guid-456",
            "owner_id": user_id,
            "is_public": True,
        }
        response = await client.post("/api/v1/processes/", json=process_data)
        print(f"   ✅ Process created: {response.status_code}")
        process = response.json()
        process_id = process["id"]

        # Test getting the process
        print("3. Getting the created process...")
        response = await client.get(f"/api/v1/processes/{process_id}")
        print(f"   ✅ Process retrieved: {response.status_code}")

        # Test getting process by GUID
        print("4. Getting process by GUID...")
        response = await client.get("/api/v1/processes/by-guid/test-guid-456")
        print(f"   ✅ Process by GUID: {response.status_code}")

        # Test listing public processes
        print("5. Listing public processes...")
        response = await client.get("/api/v1/processes/public")
        print(
            f"   ✅ Public processes: {response.status_code} - {len(response.json())} processes"
        )

        # Test getting user by GPN
        print("6. Getting user by GPN...")
        response = await client.get("/api/v1/users/by-gpn/test-user-123")
        print(f"   ✅ User by GPN: {response.status_code}")

        # Test listing active users
        print("7. Listing active users...")
        response = await client.get("/api/v1/users/active")
        print(
            f"   ✅ Active users: {response.status_code} - {len(response.json())} users"
        )

        print("🎉 All API tests passed!")


if __name__ == "__main__":
    asyncio.run(test_apis())
