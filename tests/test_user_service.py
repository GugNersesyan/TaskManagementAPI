import pytest
from unittest.mock import patch

from app.services.user_service import (
    authenticate_user,
    create_user,
    get_user_by_id,
)
from app.core.security import hash_password


class TestAuthenticateUser:
    def test_authenticate_user_success(self, mock_db, test_user):
        test_user.hashed_password = hash_password("testpassword")
        mock_db.query.return_value.filter.return_value.first.return_value = test_user

        result = authenticate_user(mock_db, "test@example.com", "testpassword")

        assert result == test_user
        mock_db.query.assert_called_once()

    def test_authenticate_user_user_not_found(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        result = authenticate_user(mock_db, "notfound@example.com", "password")

        assert result is None

    def test_authenticate_user_wrong_password(self, mock_db, test_user):
        test_user.hashed_password = hash_password("correctpassword")
        mock_db.query.return_value.filter.return_value.first.return_value = test_user

        result = authenticate_user(mock_db, "test@example.com", "wrongpassword")

        assert result is None


class TestCreateUser:
    def test_create_user_success(self, mock_db):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.user_service.hash_password") as mock_hash:
            mock_hash.return_value = "hashed_password"
            user = create_user(mock_db, "newuser", "new@example.com", "password123")

        assert user.username == "newuser"
        assert user.email == "new@example.com"
        mock_db.add.assert_called_once()
        mock_db.commit.assert_called_once()
        mock_db.refresh.assert_called_once()

    def test_create_user_duplicate_username(self, mock_db, test_user):
        mock_db.query.return_value.filter.return_value.first.return_value = test_user

        with pytest.raises(ValueError, match="Username or email already registered"):
            create_user(mock_db, "testuser", "new@example.com", "password123")

    def test_create_user_duplicate_email(self, mock_db, test_user):
        mock_db.query.return_value.filter.return_value.first.return_value = test_user

        with pytest.raises(ValueError, match="Username or email already registered"):
            create_user(mock_db, "newuser", "test@example.com", "password123")


class TestGetUserById:
    def test_get_user_by_id_found(self, mock_db, test_user):
        mock_db.get.return_value = test_user

        result = get_user_by_id(mock_db, "1")

        assert result == test_user

    def test_get_user_by_id_not_found(self, mock_db):
        mock_db.get.return_value = None

        result = get_user_by_id(mock_db, "999")

        assert result is None
