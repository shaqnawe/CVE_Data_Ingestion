import os

os.environ["REDIS_URL"] = "redis://localhost:6379/0"


def test_trigger_etl(client, auth_headers):
    response = client.post("/trigger-etl", headers=auth_headers)
    # Accept 200 or 202 depending on implementation
    assert response.status_code in (200, 202)
    data = response.json()
    assert "message" in data
