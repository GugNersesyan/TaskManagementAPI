from pydantic import BaseModel, Field
from typing import Optional
from datetime import datetime

from app.models.task import TaskStatus, TaskPriority

class TaskBase(BaseModel):
    title: str = Field(..., max_length=255)
    description: str
    priority: TaskPriority = TaskPriority.medium

class TaskCreate(TaskBase):
    assigned_to: Optional[int] = None

class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, max_length=255)
    description: Optional[str] = None
    status: Optional[TaskStatus] = None
    priority: Optional[TaskPriority] = None
    assigned_to: Optional[int] = None

class TaskResponse(TaskBase):
    id: int
    status: TaskStatus
    assigned_to: Optional[int]
    created_by: int
    created_at: datetime
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True
