"""REST API router for Task Management."""

from uuid import UUID
from fastapi import APIRouter, HTTPException, status
from app.models import Task, TaskCreate, TaskUpdate
from app.persistence import repository

router = APIRouter(prefix="/tasks", tags=["tasks"])


@router.get("", response_model=list[Task])
def get_tasks() -> list[Task]:
    return repository.list_all()


@router.post("", response_model=Task, status_code=status.HTTP_201_CREATED)
def create_task(payload: TaskCreate) -> Task:
    return repository.create(payload)


@router.get("/{task_id}", response_model=Task)
def get_task(task_id: UUID) -> Task:
    task = repository.get_by_id(task_id)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.put("/{task_id}", response_model=Task)
def update_task(task_id: UUID, payload: TaskUpdate) -> Task:
    task = repository.update(task_id, payload)
    if not task:
        raise HTTPException(status_code=404, detail="Task not found")
    return task


@router.delete("/{task_id}")
def delete_task(task_id: UUID) -> dict[str, str]:
    deleted = repository.delete(task_id)
    if not deleted:
        raise HTTPException(status_code=404, detail="Task not found")
    return {"status": "success", "id": str(task_id)}
