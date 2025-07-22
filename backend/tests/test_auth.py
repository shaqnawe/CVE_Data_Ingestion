def test_register(client):
    reg_data = {
        "username": "testuser",
        "email": "testuser@example.com",
        "password": "testpassword",
        "role": "admin",
    }
    response = client.post("/auth/register", json=reg_data)
    print("Register response:", response.status_code, response.text)
    assert response.status_code == 200


def test_login(client):
    login_data = {"email": "testuser@example.com", "password": "testpassword"}
    response = client.post("/auth/login", json=login_data)
    print("Login response:", response.status_code, response.text, response.json())
    token = response.json().get("access_token")
    print("Token:", token)
    assert token
    assert response.status_code == 200


def test_get_current_user_info(client, auth_headers):
    print("Auth headers:", auth_headers)
    response = client.get("/auth/me", headers=auth_headers)
    print("Me response:", response.status_code, response.text)
    assert response.status_code == 200
    assert response.json()["username"] == "testuser"
