

class TestCreateTask:
    def test_create_task_success(self, client, user_token):
        response = client.post(
            "/api/tasks/",
            json={
                "title": "New Task",
                "description": "Task Description",
                "priority": "high"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "New Task"
        assert data["description"] == "Task Description"
        assert data["priority"] == "high"
        assert data["status"] == "pending"

    def test_create_task_unauthorized(self, client):
        response = client.post(
            "/api/tasks/",
            json={
                "title": "New Task",
                "description": "Task Description",
                "priority": "high"
            }
        )
        assert response.status_code == 401

    def test_create_task_assign_without_admin(self, client, user_token):
        response = client.post(
            "/api/tasks/",
            json={
                "title": "New Task",
                "description": "Task Description",
                "priority": "high",
                "assigned_to": 999
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 403

    def test_create_task_assign_with_admin(self, client, admin_token, test_user_db):
        response = client.post(
            "/api/tasks/",
            json={
                "title": "New Task",
                "description": "Task Description",
                "priority": "high",
                "assigned_to": test_user_db.id
            },
            headers={"Authorization": f"Bearer {admin_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["assigned_to"] == test_user_db.id


class TestListTasks:
    def test_list_tasks_success(self, client, user_token):
        response = client.get(
            "/api/tasks/",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        assert isinstance(response.json(), list)

    def test_list_tasks_unauthorized(self, client):
        response = client.get("/api/tasks/")
        assert response.status_code == 401

    def test_list_tasks_filter_by_status(self, client, user_token):
        response = client.get(
            "/api/tasks/?status=pending",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200


class TestGetTask:
    def test_get_task_success(self, client, user_token):
        create_response = client.post(
            "/api/tasks/",
            json={
                "title": "Task to Get",
                "description": "Description",
                "priority": "medium"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        task_id = create_response.json()["id"]

        response = client.get(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Task to Get"

    def test_get_task_not_found(self, client, user_token):
        response = client.get(
            "/api/tasks/99999",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 404


class TestUpdateTask:
    def test_update_task_success(self, client, user_token):
        create_response = client.post(
            "/api/tasks/",
            json={
                "title": "Original Title",
                "description": "Original Description",
                "priority": "low"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        task_id = create_response.json()["id"]

        response = client.put(
            f"/api/tasks/{task_id}",
            json={
                "title": "Updated Title",
                "status": "in_progress"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 200
        data = response.json()
        assert data["title"] == "Updated Title"
        assert data["status"] == "in_progress"

    def test_update_task_unauthorized(self, client):
        response = client.put(
            "/api/tasks/1",
            json={"title": "Updated Title"}
        )
        assert response.status_code == 401

    def test_update_task_not_owner(self, client, user_token, user2_token, test_user_db):
        user_token_to_create = user_token

        create_response = client.post(
            "/api/tasks/",
            json={
                "title": "User Task",
                "description": "Description",
                "priority": "low"
            },
            headers={"Authorization": f"Bearer {user_token_to_create}"}
        )
        task_id = create_response.json()["id"]

        response = client.put(
            f"/api/tasks/{task_id}",
            json={"title": "Hacked Title"},
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 403

    def test_update_invalid_status_transition(self, client, user_token):
        create_response = client.post(
            "/api/tasks/",
            json={
                "title": "Task",
                "description": "Description",
                "priority": "low"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        task_id = create_response.json()["id"]

        client.put(
            f"/api/tasks/{task_id}",
            json={"status": "completed"},
            headers={"Authorization": f"Bearer {user_token}"}
        )

        response = client.put(
            f"/api/tasks/{task_id}",
            json={"status": "pending"},
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 400


class TestDeleteTask:
    def test_delete_task_success(self, client, user_token):
        create_response = client.post(
            "/api/tasks/",
            json={
                "title": "Task to Delete",
                "description": "Description",
                "priority": "low"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        task_id = create_response.json()["id"]

        response = client.delete(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {user_token}"}
        )
        assert response.status_code == 204

    def test_delete_task_unauthorized(self, client):
        response = client.delete("/api/tasks/1")
        assert response.status_code == 401

    def test_delete_task_not_owner(self, client, user_token, user2_token, test_user_db):
        create_response = client.post(
            "/api/tasks/",
            json={
                "title": "Task",
                "description": "Description",
                "priority": "low"
            },
            headers={"Authorization": f"Bearer {user_token}"}
        )
        task_id = create_response.json()["id"]

        response = client.delete(
            f"/api/tasks/{task_id}",
            headers={"Authorization": f"Bearer {user2_token}"}
        )
        assert response.status_code == 403
