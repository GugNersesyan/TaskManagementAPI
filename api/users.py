from fastapi import APIRouter, Depends

from app.models.user import User
from app.api.deps import require_roles
from app.core.security import Role
from app.api.deps import get_current_user

router = APIRouter(prefix="/users", tags=['Users'])

@router.get('/', dependencies=[Depends(require_roles(Role.ADMIN))])
def list_users():
    return {'users': "all users"}

@router.delete("/{user_id}", dependencies=[Depends(require_roles(Role.ADMIN))])
def delete_user(user_id: int):
    return {'status': 'deleted'}

@router.get("/me")
def read_me(user: User = Depends(get_current_user)):
    return {
        "id": user.id,
        "username": user.username,
        "email": user.email,
        "role": user.role,
    }
