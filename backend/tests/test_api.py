import pytest
import httpx
from backend.app.main import app


@pytest.mark.asyncio
async def test_health_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/health")
        assert response.status_code == 200
        data = response.json()
        assert data["status"] == "healthy"
        assert "models" in data
        assert "thresholds" in data


@pytest.mark.asyncio
async def test_triage_flow_color_mismatch():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "order_id": "ORD-TEST-101",
            "sku": "DHG-TEST-SKU",
            "vendor_id": "VND-TEST-01",
            "raw_text": "Color picture me royal blue tha par aaya bilkul faded washed out lag raha hai"
        }
        response = await client.post("/api/v1/triage", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["primary_category"] == "COLOR_MISMATCH"
        assert data["order_id"] == "ORD-TEST-101"
        assert data["routing_path"] in ["PATH_A", "PATH_B"]


@pytest.mark.asyncio
async def test_triage_spam_rejection():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        payload = {
            "order_id": "ORD-SPAM-999",
            "sku": "DHG-TEST-SKU",
            "vendor_id": "VND-TEST-01",
            "raw_text": "..."
        }
        response = await client.post("/api/v1/triage", json=payload)
        assert response.status_code == 201
        data = response.json()
        assert data["status"] == "FLAGGED_FOR_MANUAL_REVIEW"
        assert data["sub_category"] == "rejected_spam"


@pytest.mark.asyncio
async def test_analytics_summary_endpoint():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as client:
        response = await client.get("/api/v1/triage/analytics/summary")
        assert response.status_code == 200
        data = response.json()
        assert "total_returns_processed" in data
        assert "unclassified_other_reduction_pct" in data
