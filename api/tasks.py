from typing import List, Optional
from fastapi import APIRouter, Depends,  status, Query, WebSocket, WebSocketDisconnect
from sqlalchemy.orm import Session

from app.db.session import get_db, SessionLocal
from app.models.user import User
from app.models.task import Task, TaskStatus
from app.schemas.task import TaskCreate, TaskUpdate, TaskResponse
from app.services.task_service import TaskService, manager
from app.api.deps import get_current_user
from app.core.security import decode_token

router = APIRouter(
    prefix="/tasks",
    tags=['Tasks']
)

@router.websocket("/ws/tasks")
async def websocket_endpoint(
    websocket: WebSocket,
    token: str = Query(...)
):
    payload = decode_token(token)

    if not payload or payload.get("type") != "access":
        await websocket.close(code=1008)
        return

    user_id = payload.get("sub")

    if not user_id:
        await websocket.close(code=1008)
        return

    try:
        user_id = int(user_id)
    except (TypeError, ValueError):
        await websocket.close(code=1008)
        return

    with SessionLocal() as db:
        user = db.query(User).filter(User.id == user_id).first()

        if not user:
            await websocket.close(code=1008)
            return

    await manager.connect(websocket, user.id)

    try:
        while True:
            await websocket.receive_text()
    except WebSocketDisconnect:
        manager.disconnect(websocket, user.id)


    

@router.post('/', response_model=TaskResponse)
def create_task(
    task_data: TaskCreate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    task = TaskService.create_task(db, task_data, current_user)
    return task

@router.get("/", response_model=List[TaskResponse])
def list_tasks(
    status: Optional[TaskStatus] = Query(None),
    skip: int = Query(0, ge=0),
    limit: int = Query(10, ge=1, le=100),
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    query = db.query(Task)

    if status:
        query = query.filter(Task.status == status)

    tasks = query.offset(skip).limit(limit).all()
    return tasks

@router.get("/{task_id}", response_model=TaskResponse)
def get_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    task = TaskService.get_task(db, task_id)
    return task

@router.put("/{task_id}", response_model=TaskResponse)
def update_task(
    task_id: int,
    update_data: TaskUpdate,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    task = TaskService.get_task(db, task_id)
    updated_task = TaskService.update_task(db, task, update_data, current_user)
    return updated_task

@router.delete("/{task_id}", status_code=status.HTTP_204_NO_CONTENT)
def delete_task(
    task_id: int,
    db: Session = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    
    task = TaskService.get_task(db, task_id)
    TaskService.delete_task(db, task, current_user)

    return