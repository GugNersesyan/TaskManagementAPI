from typing import Optional, cast
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
import json
import asyncio

from app.core.connection_manager import ConnectionManager
from app.core.cache import redis_client
from app.models.task import Task, TaskStatus
from app.models.user import User
from app.schemas.task import TaskCreate, TaskUpdate
from app.core.security import Role

CACHE_TTL_TASK = 300

manager = ConnectionManager()


class TaskService:

    @staticmethod
    def _validate_status_transition(old_status: TaskStatus, new_status: TaskStatus):
        if old_status == TaskStatus.completed and new_status != TaskStatus.completed:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail='Cannot change status after completion'
            )
        if old_status == TaskStatus.pending and new_status not in [TaskStatus.in_progress, TaskStatus.completed]:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail="Invalid status transition"
            )

    @staticmethod
    def create_task(db: Session, task_data: TaskCreate, current_user: User) -> Task:
        task = Task(
            title=task_data.title,
            description=task_data.description,
            priority=task_data.priority,
            created_by=current_user.id,
        )

        if task_data.assigned_to:
            if current_user.role != Role.ADMIN:
                raise HTTPException(
                    status_code=status.HTTP_403_FORBIDDEN,
                    detail="Only admins can assign tasks"
                )
            task.assigned_to = task_data.assigned_to

        try:
            db.add(task)
            db.commit()
            db.refresh(task)
        except Exception:
            db.rollback()
            raise

        redis_client.delete('tasks:all')
        redis_client.setex(
            f"task:{task.id}",
            CACHE_TTL_TASK,
            json.dumps({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status.value,
                "created_by": task.created_by,
                "assigned_to": task.assigned_to
            })
        )

        asyncio.create_task(manager.broadcast(json.dumps({
            "event": "task_created",
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status.value,
                "created_by": task.created_by,
                "assigned_to": task.assigned_to
            }
        })))

        return task

    @staticmethod
    def get_task(db: Session, task_id: int) -> Task:
        cache_key = f'task:{task_id}'
        cached = cast(Optional[str], redis_client.get(cache_key))

        if cached:
            json.loads(cached)
            task = db.query(Task).filter(Task.id == task_id).first()
            if task:
                return task

        task = db.query(Task).filter(Task.id == task_id).first()
        if not task:
            raise HTTPException(
                status_code=status.HTTP_404_NOT_FOUND,
                detail='Task not found'
            )

        redis_client.setex(
            cache_key,
            CACHE_TTL_TASK,
            json.dumps({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status.value,
                "created_by": task.created_by,
                "assigned_to": task.assigned_to
            })
        )
        return task

    @staticmethod
    def update_task(db: Session, task: Task, update_data: TaskUpdate, current_user: User) -> Task:
        if current_user.id != task.created_by and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to update this task"
            )

        update_dict = update_data.dict(exclude_unset=True)

        if 'status' in update_dict:
            TaskService._validate_status_transition(
                old_status=task.status,
                new_status=update_dict['status']
            )

        if 'assigned_to' in update_dict and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Only admins can reassign tasks"
            )

        for field, value in update_dict.items():
            setattr(task, field, value)

        try:
            db.commit()
            db.refresh(task)
        except Exception:
            db.rollback()
            raise

        redis_client.delete(f"task:{task.id}")
        redis_client.delete("tasks:all")
        redis_client.setex(
            f"task:{task.id}",
            CACHE_TTL_TASK,
            json.dumps({
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status.value,
                "created_by": task.created_by,
                "assigned_to": task.assigned_to
            })
        )

        asyncio.create_task(manager.broadcast(json.dumps({
            "event": "task_updated",
            "task": {
                "id": task.id,
                "title": task.title,
                "description": task.description,
                "priority": task.priority,
                "status": task.status.value,
                "created_by": task.created_by,
                "assigned_to": task.assigned_to
            }
        })))

        return task

    @staticmethod
    def delete_task(db: Session, task: Task, current_user: User) -> None:
        if current_user.id != task.created_by and current_user.role != Role.ADMIN:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail="Not allowed to delete this task"
            )

        try:
            db.delete(task)
            db.commit()
        except Exception:
            db.rollback()
            raise

        redis_client.delete(f'task:{task.id}')
        redis_client.delete("tasks:all")

        asyncio.create_task(manager.broadcast(json.dumps({
            "event": "task_deleted",
            "task": {"id": task.id, "title": task.title}
        })))
