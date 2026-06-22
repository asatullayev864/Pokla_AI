from fastapi import APIRouter, HTTPException, status

from database.db import (
    list_admins,
    create_user,
    get_admin_by_id,
    update_admin,
    delete_admin,
    get_user_by_username,
)
from auth.security import hash_password
from api.schemas import AdminCreate, AdminUpdate, AdminResponse

# Bu router main.py da require_superadmin dependency bilan ulanadi,
# shu sababli bu yerda har bir endpointda alohida tekshirish shart emas.
router = APIRouter(prefix="/admins", tags=["Admins"])


@router.get("/", response_model=list[AdminResponse])
def get_admins():
    return list_admins()


@router.post("/", response_model=AdminResponse, status_code=status.HTTP_201_CREATED)
def add_admin(data: AdminCreate):
    if get_user_by_username(data.username):
        raise HTTPException(status_code=400, detail="Bu login allaqachon band")

    user = create_user(
        username=data.username,
        password_hash=hash_password(data.password),
        role="admin",
        full_name=data.full_name,
    )
    if user is None:
        raise HTTPException(status_code=400, detail="Admin yaratib bo'lmadi")

    return user


@router.put("/{admin_id}", response_model=AdminResponse)
def edit_admin(admin_id: int, data: AdminUpdate):
    if not get_admin_by_id(admin_id):
        raise HTTPException(status_code=404, detail="Admin topilmadi")

    password_hash = hash_password(data.password) if data.password else None

    updated = update_admin(
        admin_id,
        password_hash=password_hash,
        full_name=data.full_name,
        is_active=data.is_active,
    )
    return updated


@router.delete("/{admin_id}", status_code=status.HTTP_204_NO_CONTENT)
def remove_admin(admin_id: int):
    if not delete_admin(admin_id):
        raise HTTPException(status_code=404, detail="Admin topilmadi")
    
