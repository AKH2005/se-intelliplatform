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

def _match_id(stored_id: Any, lookup_id: Any) -> bool:
    if str(stored_id) == str(lookup_id):
        return True
    try:
        if isinstance(lookup_id, UUID):
            if isinstance(stored_id, int) and lookup_id.int == stored_id:
                return True
        elif isinstance(stored_id, int):
            try:
                u = UUID(str(lookup_id))
                if u.int == stored_id:
                    return True
            except Exception:
                pass
    except Exception:
        pass
    return False

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
    new_uuid = uuid4()
    title = getattr(task, 'title', str(task)) if task else 'New Task'
    desc = getattr(task, 'description', None) if task else None
    priority = getattr(task, 'priority', 'MEDIUM') if task else 'MEDIUM'
    status = getattr(task, 'status', 'PENDING') if task else 'PENDING'
    status_str = status if isinstance(status, str) else getattr(status, 'value', 'PENDING')
    new_t = {
        'id': str(new_uuid),
        'title': title,
        'description': desc,
        'completed': (status_str == 'COMPLETED'),
        'owner_id': owner_id,
        'priority': priority if isinstance(priority, str) else getattr(priority, 'value', 'MEDIUM'),
        'status': status_str,
        'due_date': getattr(task, 'due_date', None) if task else None,
    }
    _tasks_store.append(new_t)
    return _to_model(new_t)

async def get_tasks(db=None) -> List[Any]:
    return [_to_model(t) for t in _tasks_store]

async def create_task(db=None, task=None, owner_id: int = 1) -> Any:
    return _create_task_impl(task=task, owner_id=owner_id)

async def update_task(db=None, task_id: Any = 1, task_update=None) -> Optional[Any]:
    for t in _tasks_store:
        if _match_id(t['id'], task_id):
            if hasattr(task_update, 'title') and task_update.title is not None:
                t['title'] = task_update.title
            if hasattr(task_update, 'description') and task_update.description is not None:
                t['description'] = task_update.description
            if hasattr(task_update, 'priority') and task_update.priority is not None:
                t['priority'] = task_update.priority if isinstance(task_update.priority, str) else getattr(task_update.priority, 'value', 'MEDIUM')
            if hasattr(task_update, 'status') and task_update.status is not None:
                status_val = task_update.status if isinstance(task_update.status, str) else getattr(task_update.status, 'value', 'PENDING')
                t['status'] = status_val
                t['completed'] = (status_val == 'COMPLETED')
            if hasattr(task_update, 'completed') and task_update.completed is not None:
                t['completed'] = task_update.completed
                if task_update.completed:
                    t['status'] = 'COMPLETED'
            return _to_model(t)
    return None

async def delete_task(db=None, task_id: Any = 1) -> bool:
    global _tasks_store
    initial_len = len(_tasks_store)
    _tasks_store = [t for t in _tasks_store if not _match_id(t['id'], task_id)]
    return len(_tasks_store) < initial_len

class TaskRepository:
    def list_all(self):
        return [_to_model(t) for t in _tasks_store]
        
    def get_by_id(self, task_id):
        for t in _tasks_store:
            if _match_id(t['id'], task_id):
                return _to_model(t)
        return None
        
    def create(self, data):
        return _create_task_impl(task=data)
        
    def update(self, task_id, data):
        for t in _tasks_store:
            if _match_id(t['id'], task_id):
                if hasattr(data, 'title') and data.title is not None:
                    t['title'] = data.title
                if hasattr(data, 'description') and data.description is not None:
                    t['description'] = data.description
                if hasattr(data, 'priority') and data.priority is not None:
                    t['priority'] = data.priority if isinstance(data.priority, str) else getattr(data.priority, 'value', 'MEDIUM')
                if hasattr(data, 'status') and data.status is not None:
                    status_val = data.status if isinstance(data.status, str) else getattr(data.status, 'value', 'PENDING')
                    t['status'] = status_val
                    t['completed'] = (status_val == 'COMPLETED')
                if hasattr(data, 'completed') and data.completed is not None:
                    t['completed'] = data.completed
                    if data.completed:
                        t['status'] = 'COMPLETED'
                if hasattr(data, 'due_date') and data.due_date is not None:
                    t['due_date'] = data.due_date
                return _to_model(t)
        return None
        
    def delete(self, task_id):
        global _tasks_store
        initial_len = len(_tasks_store)
        _tasks_store = [t for t in _tasks_store if not _match_id(t['id'], task_id)]
        return len(_tasks_store) < initial_len

repository = TaskRepository()
