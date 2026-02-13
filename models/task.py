from __future__ import annotations
from app.db.base_class import Base
from sqlalchemy import ForeignKey, String, Text, DateTime, Enum
from sqlalchemy.orm import relationship, Mapped, mapped_column
from datetime import datetime
import enum
from typing import Optional, TYPE_CHECKING

if TYPE_CHECKING:
    from app.models.user import User

class TaskStatus(str, enum.Enum):
    pending = 'pending'
    in_progress = 'in_progress'
    completed = 'completed'

class TaskPriority(str, enum.Enum):
    low = 'low'
    medium = 'medium'
    high = 'high'

class Task(Base):
    __tablename__ = 'tasks'

    id: Mapped[int] = mapped_column(primary_key=True, index=True)
    title: Mapped[str] = mapped_column(String(255), nullable=False)
    description: Mapped[str] = mapped_column(Text, nullable=False)

    status: Mapped[TaskStatus] = mapped_column(
        Enum(TaskStatus),
        default=TaskStatus.pending,
        nullable=False,
        index=True,
    )

    priority: Mapped[TaskPriority] = mapped_column(
        Enum(TaskPriority),
        default=TaskPriority.medium,
        nullable=False,
        index=True,
    )

    assigned_to: Mapped[Optional[int]] = mapped_column(
        ForeignKey("users.id"),
        nullable=True,
        index=True,
    )

    created_by: Mapped[int] = mapped_column(
        ForeignKey("users.id"),
        nullable=False,
        index=True,
    )

    created_at: Mapped[datetime] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        nullable=False,
    )
    
    updated_at: Mapped[Optional[datetime]] = mapped_column(
        DateTime,
        default=datetime.utcnow,
        onupdate=datetime.utcnow,
    )

    assignee: Mapped[Optional['User']] = relationship(
        "User",
        foreign_keys=[assigned_to],
        backref="assigned_tasks",
    )

    creator: Mapped['User'] = relationship(
        'User',
        foreign_keys=[created_by],
        backref="created_tasks",
    )

    def __repr__(self) -> str:
        return f"<Task id={self.id} title={self.title} status={self.status}>"