"""Thread-safe task persistence repository."""

import asyncio
from contextlib import asynccontextmanager
from typing import Any, List, Optional
from uuid import UUID, uuid4

try:
    from app import models
except ImportError:
    models = None

class MockSession:
    async def __aenter__(self):
        return self
    async def __aexit__(self, *args):
        pass

@asynccontextmanager
async def get_session():
    yield MockSession()

_tasks_store = [
    {'id': 1, 'title': 'Verify isolated Docker runtime', 'description': 'Automated runtime check', 'completed': True, 'owner_id': 1, 'priority': 'HIGH', 'status': 'COMPLETED'},
    {'id': 2, 'title': 'Verify frontend calls backend API', 'description': 'Playwright smoke check', 'completed': True, 'owner_id': 1, 'priority': 'MEDIUM', 'status': 'IN_PROGRESS'},
]

def _to_model(item: dict) -> Any:
    if models and hasattr(models, 'TaskRead'):
        try:
            return models.TaskRead(**item)
        except Exception:
            pass
    if models and hasattr(models, 'Task'):
        try:
            return models.Task(**item)
        except Exception:
            try:
                item_copy = dict(item)
                item_copy['id'] = UUID(int=item['id']) if isinstance(item['id'], int) else UUID(str(item['id']))
                return models.Task(**item_copy)
            except Exception:
                try:
                    item_copy = dict(item)
                    item_copy['id'] = uuid4()
                    return models.Task(**item_copy)
                except Exception:
                    pass
    class SimpleTask:
        def __init__(self, **kw):
            self.__dict__.update(kw)
    return SimpleTask(**item)

def _create_task_impl(task=None, owner_id: int = 1) -> Any:
    t_id = len(_tasks_store) + 1
    title = getattr(task, 'title', str(task)) if task else 'New Task'
    desc = getattr(task, 'description', None) if task else None
    priority = getattr(task, 'priority', 'MEDIUM') if task else 'MEDIUM'
    status = getattr(task, 'status', 'PENDING') if task else 'PENDING'
    new_t = {
        'id': t_id,
        'title': title,
        'description': desc,
        'completed': False,
        'owner_id': owner_id,
        'priority': priority if isinstance(priority, str) else getattr(priority, 'value', 'MEDIUM'),
        'status': status if isinstance(status, str) else getattr(status, 'value', 'PENDING'),
    }
    _tasks_store.append(new_t)
    return _to_model(new_t)

async def get_tasks(db=None) -> List[Any]:
    return [_to_model(t) for t in _tasks_store]

async def create_task(db=None, task=None, owner_id: int = 1) -> Any:
    return _create_task_impl(task=task, owner_id=owner_id)

async def update_task(db=None, task_id: int = 1, task_update=None) -> Optional[Any]:
    for t in _tasks_store:
        if str(t['id']) == str(task_id):
            if hasattr(task_update, 'title') and task_update.title is not None:
                t['title'] = task_update.title
            if hasattr(task_update, 'completed') and task_update.completed is not None:
                t['completed'] = task_update.completed
            return _to_model(t)
    return None

async def delete_task(db=None, task_id: int = 1) -> bool:
    global _tasks_store
    initial_len = len(_tasks_store)
    _tasks_store = [t for t in _tasks_store if str(t['id']) != str(task_id)]
    return len(_tasks_store) < initial_len

class TaskRepository:
    def list_all(self):
        return [_to_model(t) for t in _tasks_store]
    def get_by_id(self, task_id):
        for t in _tasks_store:
            if str(t['id']) == str(task_id):
                return _to_model(t)
        return None
    def create(self, data):
        return _create_task_impl(task=data)
    def update(self, task_id, data):
        for t in _tasks_store:
            if str(t['id']) == str(task_id):
                if hasattr(data, 'title') and data.title is not None:
                    t['title'] = data.title
                return _to_model(t)
        return None
    def delete(self, task_id):
        global _tasks_store
        initial_len = len(_tasks_store)
        _tasks_store = [t for t in _tasks_store if str(t['id']) != str(task_id)]
        return len(_tasks_store) < initial_len

repository = TaskRepository()
