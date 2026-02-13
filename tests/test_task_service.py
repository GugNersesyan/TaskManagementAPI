import pytest
from unittest.mock import MagicMock, patch
from fastapi import HTTPException

from app.services.task_service import TaskService
from app.models.task import TaskStatus, TaskPriority
from app.schemas.task import TaskCreate, TaskUpdate


@pytest.fixture
def mock_asyncio():
    with patch("app.services.task_service.asyncio") as mock:
        mock.create_task = MagicMock()
        yield mock


class TestValidateStatusTransition:
    def test_validate_status_completed_to_pending_fails(self):
        with pytest.raises(HTTPException) as exc_info:
            TaskService._validate_status_transition(
                TaskStatus.completed, TaskStatus.pending
            )
        assert exc_info.value.status_code == 400
        assert "Cannot change status after completion" in exc_info.value.detail

    def test_validate_status_completed_to_in_progress_fails(self):
        with pytest.raises(HTTPException) as exc_info:
            TaskService._validate_status_transition(
                TaskStatus.completed, TaskStatus.in_progress
            )
        assert exc_info.value.status_code == 400

    def test_validate_status_pending_to_completed_valid(self):
        TaskService._validate_status_transition(
            TaskStatus.pending, TaskStatus.completed
        )

    def test_validate_status_pending_to_in_progress_valid(self):
        TaskService._validate_status_transition(
            TaskStatus.pending, TaskStatus.in_progress
        )

    def test_validate_status_in_progress_to_completed_valid(self):
        TaskService._validate_status_transition(
            TaskStatus.in_progress, TaskStatus.completed
        )

    def test_validate_status_pending_to_pending_invalid(self):
        with pytest.raises(HTTPException) as exc_info:
            TaskService._validate_status_transition(
                TaskStatus.pending, TaskStatus.pending
            )
        assert exc_info.value.status_code == 400
        assert "Invalid status transition" in exc_info.value.detail


class TestCreateTask:
    def test_create_task_success(self, mock_db, mock_redis_client, test_user, mock_asyncio):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        def set_task_refresh(task):
            task.id = 1
            task.status = TaskStatus.pending

        mock_db.refresh.side_effect = set_task_refresh

        task_data = TaskCreate(
            title="New Task",
            description="New Description",
            priority=TaskPriority.high
        )

        with patch("app.services.task_service.redis_client", mock_redis_client):
            task = TaskService.create_task(mock_db, task_data, test_user)

        assert task.title == "New Task"
        assert task.description == "New Description"
        assert task.priority == TaskPriority.high
        assert task.created_by == test_user.id

    def test_create_task_assign_to_non_admin_fails(self, mock_db, test_user):
        task_data = TaskCreate(
            title="New Task",
            description="New Description",
            priority=TaskPriority.high,
            assigned_to=2
        )

        with pytest.raises(HTTPException) as exc_info:
            TaskService.create_task(mock_db, task_data, test_user)
        
        assert exc_info.value.status_code == 403
        assert "Only admins can assign tasks" in exc_info.value.detail

    def test_create_task_assign_to_admin_success(self, mock_db, mock_redis_client, test_admin_user, mock_asyncio):
        def set_task_refresh(task):
            task.id = 1
            task.status = TaskStatus.pending

        mock_db.refresh.side_effect = set_task_refresh

        task_data = TaskCreate(
            title="New Task",
            description="New Description",
            priority=TaskPriority.high,
            assigned_to=2
        )

        with patch("app.services.task_service.redis_client", mock_redis_client):
            task = TaskService.create_task(mock_db, task_data, test_admin_user)

        assert task.assigned_to == 2


class TestGetTask:
    def test_get_task_from_db(self, mock_db, mock_redis_client, test_task):
        mock_db.query.return_value.filter.return_value.first.return_value = test_task

        with patch("app.services.task_service.redis_client", mock_redis_client):
            task = TaskService.get_task(mock_db, 1)

        assert task == test_task

    def test_get_task_not_found(self, mock_db, mock_redis_client):
        mock_db.query.return_value.filter.return_value.first.return_value = None

        with patch("app.services.task_service.redis_client", mock_redis_client):
            with pytest.raises(HTTPException) as exc_info:
                TaskService.get_task(mock_db, 999)
        
        assert exc_info.value.status_code == 404
        assert "Task not found" in exc_info.value.detail


class TestUpdateTask:
    def test_update_task_success(self, mock_db, mock_redis_client, test_task, test_user, mock_asyncio):
        test_task.created_by = test_user.id
        mock_db.query.return_value.filter.return_value.first.return_value = test_task

        def set_task_refresh(task):
            task.status = TaskStatus.pending

        mock_db.refresh.side_effect = set_task_refresh

        update_data = TaskUpdate(title="Updated Title")

        with patch("app.services.task_service.redis_client", mock_redis_client):
            task = TaskService.update_task(mock_db, test_task, update_data, test_user)

        assert task.title == "Updated Title"

    def test_update_task_not_owner_or_admin_fails(self, mock_db, mock_redis_client, test_task, test_user):
        test_task.created_by = 999

        update_data = TaskUpdate(title="Updated Title")

        with patch("app.services.task_service.redis_client", mock_redis_client):
            with pytest.raises(HTTPException) as exc_info:
                TaskService.update_task(mock_db, test_task, update_data, test_user)
        
        assert exc_info.value.status_code == 403
        assert "Not allowed to update this task" in exc_info.value.detail

    def test_update_task_status_transition_invalid(self, mock_db, mock_redis_client, test_completed_task, test_user):
        test_completed_task.created_by = test_user.id

        update_data = TaskUpdate(status=TaskStatus.pending)

        with patch("app.services.task_service.redis_client", mock_redis_client):
            with pytest.raises(HTTPException) as exc_info:
                TaskService.update_task(mock_db, test_completed_task, update_data, test_user)
        
        assert exc_info.value.status_code == 400

    def test_update_task_reassign_non_admin_fails(self, mock_db, mock_redis_client, test_task, test_user):
        test_task.created_by = test_user.id

        update_data = TaskUpdate(assigned_to=2)

        with patch("app.services.task_service.redis_client", mock_redis_client):
            with pytest.raises(HTTPException) as exc_info:
                TaskService.update_task(mock_db, test_task, update_data, test_user)
        
        assert exc_info.value.status_code == 403
        assert "Only admins can reassign tasks" in exc_info.value.detail


class TestDeleteTask:
    def test_delete_task_success(self, mock_db, mock_redis_client, test_task, test_user, mock_asyncio):
        test_task.created_by = test_user.id

        with patch("app.services.task_service.redis_client", mock_redis_client):
            TaskService.delete_task(mock_db, test_task, test_user)

        mock_db.delete.assert_called_once_with(test_task)
        mock_db.commit.assert_called_once()

    def test_delete_task_not_owner_or_admin_fails(self, mock_db, mock_redis_client, test_task, test_user):
        test_task.created_by = 999

        with patch("app.services.task_service.redis_client", mock_redis_client):
            with pytest.raises(HTTPException) as exc_info:
                TaskService.delete_task(mock_db, test_task, test_user)
        
        assert exc_info.value.status_code == 403
        assert "Not allowed to delete this task" in exc_info.value.detail
