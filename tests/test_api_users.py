

class TestReadMe:
    def test_read_me_success(self, client, user_token):
        response = client.get(
            "/api/users/me",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert "id" in data
        assert "username" in data
        assert "email" in data
        assert "role" in data

    def test_read_me_unauthorized(self, client):
        response = client.get("/api/users/me")
        assert response.status_code == 401


class TestListUsers:
    def test_list_users_admin(self, client, admin_token):
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_list_users_regular_user(self, client, user_token):
        response = client.get(
            "/api/users/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

    def test_list_users_unauthorized(self, client):
        response = client.get("/api/users/")
        assert response.status_code == 401


class TestDeleteUser:
    def test_delete_user_admin(self, client, admin_token):
        response = client.delete(
            "/api/users/1",
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200

    def test_delete_user_regular_user(self, client, user_token):
        response = client.delete(
            "/api/users/1",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

    def test_delete_user_unauthorized(self, client):
        response = client.delete("/api/users/1")
        assert response.status_code == 401
