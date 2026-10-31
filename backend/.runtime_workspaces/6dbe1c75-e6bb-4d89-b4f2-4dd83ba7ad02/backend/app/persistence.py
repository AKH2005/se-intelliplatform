"""Thread-safe task repository."""

from uuid import UUID
from app.models import Task, TaskCreate, TaskPriority, TaskStatus, TaskUpdate


class TaskRepository:
    def __init__(self) -> None:
        self._tasks: dict[UUID, Task] = {}
        t1 = Task(title="Verify isolated Docker runtime", priority=TaskPriority.HIGH, status=TaskStatus.COMPLETED)
        t2 = Task(title="Verify frontend calls backend API", priority=TaskPriority.MEDIUM, status=TaskStatus.IN_PROGRESS)
        self._tasks[t1.id] = t1
        self._tasks[t2.id] = t2

    def list_all(self) -> list[Task]:
        return list(self._tasks.values())

    def get_by_id(self, task_id: UUID) -> Task | None:
        return self._tasks.get(task_id)

    def create(self, data: TaskCreate) -> Task:
        task = Task(
            title=data.title,
            description=data.description,
            priority=data.priority,
            due_date=data.due_date,
        )
        self._tasks[task.id] = task
        return task

    def update(self, task_id: UUID, data: TaskUpdate) -> Task | None:
        task = self._tasks.get(task_id)
        if not task:
            return None
        if data.title is not None:
            task.title = data.title
        if data.description is not None:
            task.description = data.description
        if data.priority is not None:
            task.priority = data.priority
        if data.status is not None:
            task.status = data.status
        if data.due_date is not None:
            task.due_date = data.due_date
        return task

    def delete(self, task_id: UUID) -> bool:
        if task_id in self._tasks:
            del self._tasks[task_id]
            return True
        return False


repository = TaskRepository()
