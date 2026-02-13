import pytest
from unittest.mock import patch

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)
from app.api.deps import get_current_user, require_roles
from app.core.security import Role


class TestCompleteAuthFlow:
    def test_full_auth_flow(self, client):
        register_response = client.post("/auth/register", json={
            "username": "flowuser",
            "email": "flow@example.com",
            "password": "password123"
        })
        assert register_response.status_code == 201
        register_response.json()["id"]

        login_response = client.post("/auth/login", json={
            "email": "flow@example.com",
            "password": "password123"
        })
        assert login_response.status_code == 200
        tokens = login_response.json()
        access_token = tokens["access_token"]
        refresh_token = tokens["refresh_token"]

        me_response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert me_response.status_code == 200
        assert me_response.json()["email"] == "flow@example.com"

        refresh_response = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response.status_code == 200
        new_tokens = refresh_response.json()
        new_access_token = new_tokens["access_token"]

        me_response2 = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {new_access_token}"}
        )
        assert me_response2.status_code == 200

    def test_login_then_access_protected(self, client, test_user_db):
        login_response = client.post("/auth/login", json={
            "email": test_user_db.email,
            "password": "password123"
        })
        assert login_response.status_code == 200
        access_token = login_response.json()["access_token"]

        task_response = client.post(
            "/api/tasks/",
            json={
                "title": "Protected Task",
                "description": "Testing protected access",
                "priority": "medium"
            },
            headers={"Authorization": f"Bearer {access_token}"}
        )
        assert task_response.status_code == 200
        assert task_response.json()["title"] == "Protected Task"

    def test_refresh_maintains_session(self, client, test_user_db):
        login_response = client.post("/auth/login", json={
            "email": test_user_db.email,
            "password": "password123"
        })
        refresh_token = login_response.json()["refresh_token"]

        refresh_response1 = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        refresh_response1.json()["access_token"]

        refresh_response2 = client.post("/auth/refresh", json={
            "refresh_token": refresh_token
        })
        assert refresh_response2.status_code == 200
        assert "access_token" in refresh_response2.json()


class TestTokenHandling:
    @patch("app.core.security.settings")
    def test_decode_valid_access_token(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        token = create_access_token("user123", "user")
        payload = decode_token(token)

        assert payload["sub"] == "user123"
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    @patch("app.core.security.settings")
    def test_decode_valid_refresh_token(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7

        token = create_refresh_token("user123")
        payload = decode_token(token)

        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"

    @patch("app.core.security.settings")
    def test_decode_invalid_token(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"

        payload = decode_token("invalid.jwt.token")
        assert payload == {}

    @patch("app.core.security.settings")
    def test_decode_wrong_signature(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        token = create_access_token("user123", "user")

        with patch("app.core.security.settings") as wrong_settings:
            wrong_settings.SECRET_KEY = "different-secret"
            wrong_settings.ALGORITHM = "HS256"
            payload = decode_token(token)

        assert payload == {}

    @patch("app.core.security.settings")
    def test_decode_malformed_token(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"

        payload = decode_token("not-a-token-at-all")
        assert payload == {}


class TestGetCurrentUser:
    def test_get_current_user_valid_token(self, test_db, test_user_db):
        token = create_access_token(str(test_user_db.id), test_user_db.role)

        user = get_current_user(token=token, db=test_db)

        assert user.id == test_user_db.id
        assert user.email == test_user_db.email

    def test_get_current_user_invalid_token(self, test_db):
        with pytest.raises(Exception) as exc_info:
            get_current_user(token="invalid_token", db=test_db)
        assert "Invalid token" in str(exc_info.value)

    def test_get_current_user_wrong_type(self, test_db, test_user_db):
        token = create_refresh_token(str(test_user_db.id))

        with pytest.raises(Exception) as exc_info:
            get_current_user(token=token, db=test_db)
        assert "Invalid token type" in str(exc_info.value)

    def test_get_current_user_nonexistent(self, test_db):
        token = create_access_token("99999", "user")

        with pytest.raises(Exception) as exc_info:
            get_current_user(token=token, db=test_db)
        assert "User not found" in str(exc_info.value)


class TestPasswordHandling:
    def test_password_hash_and_verify(self):
        password = "mypassword123"
        hashed = hash_password(password)

        assert verify_password(password, hashed) is True

    def test_password_hash_unique(self):
        password = "mypassword123"
        hash1 = hash_password(password)
        hash2 = hash_password(password)

        assert hash1 != hash2

    def test_password_verify_wrong(self):
        password = "mypassword123"
        hashed = hash_password(password)

        assert verify_password("wrongpassword", hashed) is False

    def test_password_verify_empty(self):
        hashed = hash_password("password")

        assert verify_password("", hashed) is False


class TestRoleBasedAccess:
    def test_require_roles_admin_allowed(self, test_db, test_admin_db):
        create_access_token(str(test_admin_db.id), test_admin_db.role)

        with patch("app.api.deps.get_current_user") as mock_get_user:
            mock_get_user.return_value = test_admin_db

            checker = require_roles(Role.ADMIN)
            result = checker(user=test_admin_db)

            assert result == test_admin_db

    def test_require_roles_regular_user_denied(self, test_db, test_user_db):
        checker = require_roles(Role.ADMIN)

        with pytest.raises(Exception):
            checker(user=test_user_db)


class TestTokenExpiration:
    @patch("app.core.security.settings")
    def test_access_token_expiry(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = -1

        token = create_access_token("user123", "user")
        payload = decode_token(token)

        assert payload == {}

    @patch("app.core.security.settings")
    def test_refresh_token_expiry(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = -1

        token = create_refresh_token("user123")
        payload = decode_token(token)

        assert payload == {}


class TestAuthenticationErrors:
    def test_login_with_expired_refresh_token(self, client):
        token = create_refresh_token("99999")

        response = client.post("/auth/refresh", json={
            "refresh_token": token
        })
        assert response.status_code == 401

    def test_access_protected_without_token(self, client):
        response = client.post("/api/tasks/", json={
            "title": "Task",
            "description": "Description",
            "priority": "medium"
        })
        assert response.status_code == 401

    def test_access_protected_with_invalid_token(self, client):
        response = client.post("/api/tasks/", json={
            "title": "Task",
            "description": "Description",
            "priority": "medium"
        }, headers={"Authorization": "Bearer invalid_token"})
        assert response.status_code == 401
