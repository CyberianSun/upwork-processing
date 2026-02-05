import pytest
from httpx import AsyncClient

from main import app


@pytest.fixture
async def client():
    async with AsyncClient(app=app, base_url="http://test") as ac:
        yield ac


@pytest.mark.asyncio
async def test_stats_endpoint(client: AsyncClient):
    response = await client.get("/jobs/stats")
    assert response.status_code == 200
    data = response.json()
    assert "total_jobs" in data
    assert "ai_related_jobs" in data


@pytest.mark.asyncio
async def test_ranked_jobs_empty(client: AsyncClient):
    response = await client.get("/jobs/ranked")
    assert response.status_code == 200
    assert isinstance(response.json(), list)