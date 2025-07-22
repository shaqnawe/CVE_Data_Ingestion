def test_list_cves(client, auth_headers):
    response = client.get("/cves/?skip=0&limit=5", headers=auth_headers)
    assert response.status_code == 200
    data = response.json()
    assert "items" in data
    assert isinstance(data["items"], list)


def test_get_cve_by_id(client, auth_headers):
    # Get a list of CVEs first
    response = client.get("/cves/?skip=0&limit=1", headers=auth_headers)
    assert response.status_code == 200
    items = response.json()["items"]
    if not items:
        return  # Skip if no CVEs in DB
    cve_id = items[0]["cve_id"]
    response = client.get(f"/cves/{cve_id}", headers=auth_headers)
    assert response.status_code == 200
    assert response.json()["cve_id"] == cve_id


def test_search_cves(client, auth_headers):
    response = client.get("/cves/search/?query=buffer&skip=0&limit=5", headers=auth_headers)
    assert response.status_code == 200
    assert isinstance(response.json(), list) 