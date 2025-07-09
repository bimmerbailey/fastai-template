import pytest
from httpx import AsyncClient


@pytest.mark.asyncio
async def test_livez(async_client: AsyncClient):
    res = await async_client.get("/livez")
    assert res.status_code == 200
    assert res.json() == {"status": "healthy"}


@pytest.mark.asyncio
async def test_readyz(async_client: AsyncClient):
    res = await async_client.get("/readyz")
    assert res.status_code == 200
    assert res.json() == {"status": "ready"}
