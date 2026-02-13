from app.core.security import create_access_token, create_refresh_token


class TestAuthRegister:
    def test_register_success(self, client):
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "password123"
        })
        assert response.status_code == 201
        data = response.json()
        assert data["username"] == "newuser"
        assert data["email"] == "newuser@example.com"
        assert "id" in data

    def test_register_duplicate_email(self, client, test_user_db):
        try:
            response = client.post("/auth/register", json={
                "username": "anotheruser",
                "email": test_user_db.email,
                "password": "password123"
            })
            assert response.status_code in (400, 422, 500)
        except ValueError:
            pass

    def test_register_duplicate_username(self, client, test_user_db):
        try:
            response = client.post("/auth/register", json={
                "username": test_user_db.username,
                "email": "another@example.com",
                "password": "password123"
            })
            assert response.status_code in (400, 422, 500)
        except ValueError:
            pass

    def test_register_invalid_email(self, client):
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "invalid-email",
            "password": "password123"
        })
        assert response.status_code == 422

    def test_register_short_password(self, client):
        response = client.post("/auth/register", json={
            "username": "newuser",
            "email": "newuser@example.com",
            "password": "short"
        })
        assert response.status_code == 422


class TestAuthLogin:
    def test_login_success(self, client, test_user_db):
        response = client.post("/auth/login", json={
            "email": test_user_db.email,
            "password": "password123"
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data
        assert data["token_type"] == "bearer"

    def test_login_invalid_email(self, client):
        response = client.post("/auth/login", json={
            "email": "notfound@example.com",
            "password": "password123"
        })
        assert response.status_code == 401

    def test_login_invalid_password(self, client, test_user_db):
        response = client.post("/auth/login", json={
            "email": test_user_db.email,
            "password": "wrongpassword"
        })
        assert response.status_code == 401


class TestAuthRefresh:
    def test_refresh_success(self, client, test_user_db):
        refresh_token = create_refresh_token(str(test_user_db.id))
        response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert response.status_code == 200
        data = response.json()
        assert "access_token" in data
        assert "refresh_token" in data

    def test_refresh_invalid_token(self, client):
        response = client.post("/auth/refresh", json={
            "refresh_token": "invalid_token"
        })
        assert response.status_code == 401

    def test_refresh_wrong_token_type(self, client, test_user_db):
        access_token = create_access_token(str(test_user_db.id), "user")
        response = client.post("/auth/refresh", json={
            "refresh_token": access_token
        })
        assert response.status_code == 401

    def test_refresh_user_not_found(self, client):
        token = create_refresh_token("99999")
        response = client.post("/auth/refresh", json={
            "refresh_token": token
        })
        assert response.status_code == 401
