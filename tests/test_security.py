from datetime import timedelta
from unittest.mock import patch

from app.core.security import (
    hash_password,
    verify_password,
    create_access_token,
    create_refresh_token,
    decode_token,
)


class TestHashPassword:
    def test_hash_password_returns_string(self):
        result = hash_password("testpassword")
        assert isinstance(result, str)
        assert result != "testpassword"

    def test_hash_password_unique(self):
        hash1 = hash_password("testpassword")
        hash2 = hash_password("testpassword")
        assert hash1 != hash2


class TestVerifyPassword:
    def test_verify_password_correct(self):
        password = "testpassword"
        hashed = hash_password(password)
        assert verify_password(password, hashed) is True

    def test_verify_password_incorrect(self):
        password = "testpassword"
        hashed = hash_password(password)
        assert verify_password("wrongpassword", hashed) is False


class TestCreateAccessToken:
    @patch("app.core.security.settings")
    def test_create_access_token_default_expiry(self, mock_settings):
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"

        token = create_access_token("user123", "user")
        
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["role"] == "user"
        assert payload["type"] == "access"

    @patch("app.core.security.settings")
    def test_create_access_token_custom_expiry(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"

        custom_delta = timedelta(minutes=60)
        token = create_access_token("user123", "user", expires_delta=custom_delta)
        
        payload = decode_token(token)
        assert payload["sub"] == "user123"


class TestCreateRefreshToken:
    @patch("app.core.security.settings")
    def test_create_refresh_token(self, mock_settings):
        mock_settings.REFRESH_TOKEN_EXPIRE_DAYS = 7
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"

        token = create_refresh_token("user123")
        
        assert isinstance(token, str)
        payload = decode_token(token)
        assert payload["sub"] == "user123"
        assert payload["type"] == "refresh"


class TestDecodeToken:
    @patch("app.core.security.settings")
    def test_decode_token_valid(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        token = create_access_token("user123", "admin")
        payload = decode_token(token)
        
        assert payload["sub"] == "user123"
        assert payload["role"] == "admin"

    @patch("app.core.security.settings")
    def test_decode_token_invalid(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"

        payload = decode_token("invalid_token")
        assert payload == {}

    @patch("app.core.security.settings")
    def test_decode_token_wrong_secret(self, mock_settings):
        mock_settings.SECRET_KEY = "test-secret-key"
        mock_settings.ALGORITHM = "HS256"
        mock_settings.ACCESS_TOKEN_EXPIRE_MINUTES = 30

        token = create_access_token("user123", "user")
        
        with patch("app.core.security.settings") as wrong_settings:
            wrong_settings.SECRET_KEY = "wrong-secret"
            wrong_settings.ALGORITHM = "HS256"
            payload = decode_token(token)
        
        assert payload == {}
