def test_elasticsearch_search(client, auth_headers):
    payload = {"query": "CVE-2024", "size": 2}
    response = client.get("/elasticsearch/search", params=payload, headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "results" in data
