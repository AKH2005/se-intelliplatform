"""Unit tests for Project Ownership Authorization & Access Control Policies."""

import uuid
import pytest
from unittest.mock import MagicMock, AsyncMock, patch

from app.api.dependencies import get_authorized_project
from app.api.v1.endpoints.projects import check_project_authorization
from app.core.exceptions import ForbiddenError, NotFoundError
from app.models.project import Project
from app.models.user import User, UserRole


def test_authorized_owner_access():
    """Verify project owner can access their own project."""
    user_id = uuid.uuid4()
    user = User(id=user_id, email="owner@example.com", role=UserRole.DEVELOPER)
    project = Project(id=uuid.uuid4(), name="My Project", owner_id=user_id)

    # Should not raise
    check_project_authorization(project, user, "access")


def test_non_owner_forbidden():
    """Verify non-owner user is forbidden from accessing another user's project."""
    user_id = uuid.uuid4()
    other_id = uuid.uuid4()
    user = User(id=user_id, email="other@example.com", role=UserRole.DEVELOPER)
    project = Project(id=uuid.uuid4(), name="Someone Else's Project", owner_id=other_id)

    with pytest.raises(ForbiddenError) as exc_info:
        check_project_authorization(project, user, "access")
    assert "permission to access this project" in str(exc_info.value.detail)


def test_admin_can_access_any_project():
    """Verify administrator can access and modify any owned project."""
    admin = User(id=uuid.uuid4(), email="admin@example.com", role=UserRole.ADMIN)
    project = Project(id=uuid.uuid4(), name="User Project", owner_id=uuid.uuid4())

    # Should not raise for read or write
    check_project_authorization(project, admin, "access")
    check_project_authorization(project, admin, "modify")


def test_unowned_project_in_development():
    """Verify unowned/demo projects are accessible in development/testing environments."""
    user = User(id=uuid.uuid4(), email="dev@example.com", role=UserRole.DEVELOPER)
    unowned_project = Project(id=uuid.uuid4(), name="Demo Project", owner_id=None)

    with patch("app.core.config.settings.ENVIRONMENT", "development"):
        check_project_authorization(unowned_project, user, "access")
        check_project_authorization(unowned_project, None, "access")


def test_unowned_project_in_production_forbidden_for_non_admin():
    """Verify unowned projects in production reject non-admin and anonymous access."""
    user = User(id=uuid.uuid4(), email="dev@example.com", role=UserRole.DEVELOPER)
    unowned_project = Project(id=uuid.uuid4(), name="System Project", owner_id=None)

    with patch("app.core.config.settings.ENVIRONMENT", "production"):
        # Anonymous user
        with pytest.raises(ForbiddenError):
            check_project_authorization(unowned_project, None, "access")

        # Standard non-admin user
        with pytest.raises(ForbiddenError) as exc_info:
            check_project_authorization(unowned_project, user, "modify")
        assert "unowned or system projects in production" in str(exc_info.value.detail)


def test_unowned_project_in_production_allowed_for_admin():
    """Verify administrator can access unowned/system projects in production."""
    admin = User(id=uuid.uuid4(), email="admin@example.com", role=UserRole.ADMIN)
    unowned_project = Project(id=uuid.uuid4(), name="System Project", owner_id=None)

    with patch("app.core.config.settings.ENVIRONMENT", "production"):
        check_project_authorization(unowned_project, admin, "modify")


@pytest.mark.asyncio
async def test_get_authorized_project_dependency():
    """Verify get_authorized_project dependency enforces ownership correctly."""
    user_id = uuid.uuid4()
    owner = User(id=user_id, email="owner@example.com", role=UserRole.DEVELOPER)
    other = User(id=uuid.uuid4(), email="other@example.com", role=UserRole.DEVELOPER)
    project_id = uuid.uuid4()
    project = Project(id=project_id, name="Dep Project", owner_id=user_id)

    mock_session = AsyncMock()
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = project
    mock_session.execute.return_value = mock_result

    # Owner access passes
    res = await get_authorized_project(project_id, current_user=owner, session=mock_session)
    assert res.id == project_id

    # Non-owner raises 403
    with pytest.raises(ForbiddenError):
        await get_authorized_project(project_id, current_user=other, session=mock_session)

    # Non-existent project raises 404
    mock_result.scalar_one_or_none.return_value = None
    with pytest.raises(NotFoundError):
        await get_authorized_project(uuid.uuid4(), current_user=owner, session=mock_session)
