"""Comprehensive Unit Tests for Safe Version Number and UUID Resolution (Milestone 4 - Workstream 3)."""

import uuid
import pytest
from unittest.mock import AsyncMock, MagicMock
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.exceptions import NotFoundError, ValidationError
from app.models.development_version import DevelopmentVersion, DevelopmentVersionStatus
from app.models.project import Project
from app.schemas.assistant import ApplyCodeChangeParams
from app.services.action_registry import validate_action_parameters
from app.services.engineering_action_service import EngineeringActionService


@pytest.fixture
def sample_project_id():
    return uuid.uuid4()


@pytest.fixture
def other_project_id():
    return uuid.uuid4()


@pytest.fixture
def sample_versions(sample_project_id, other_project_id):
    v1_id = uuid.uuid4()
    v2_id = uuid.uuid4()
    other_v1_id = uuid.uuid4()

    v1 = DevelopmentVersion(
        id=v1_id,
        project_id=sample_project_id,
        version_number=1,
        status=DevelopmentVersionStatus.SUPERSEDED,
    )
    v2 = DevelopmentVersion(
        id=v2_id,
        project_id=sample_project_id,
        version_number=2,
        status=DevelopmentVersionStatus.VERIFIED,
    )
    other_v1 = DevelopmentVersion(
        id=other_v1_id,
        project_id=other_project_id,
        version_number=1,
        status=DevelopmentVersionStatus.VERIFIED,
    )
    return {"v1": v1, "v2": v2, "other_v1": other_v1}


def test_apply_code_change_params_accepts_int_and_string_version_ids():
    """Verify ApplyCodeChangeParams accepts valid UUIDs, ints, and 'vN' strings."""
    # 1. UUID string
    u = str(uuid.uuid4())
    p1 = validate_action_parameters("APPLY_CODE_CHANGE", {
        "version_id": u,
        "reason": "Test change",
        "changes": [{"file_path": "App.tsx", "content": "export default function App() {}"}],
    })
    assert p1.version_id == u

    # 2. Integer version number
    p2 = validate_action_parameters("APPLY_CODE_CHANGE", {
        "version_id": 4,
        "reason": "Test change",
        "changes": [{"file_path": "App.tsx", "content": "export default function App() {}"}],
    })
    assert p2.version_id == 4

    # 3. String version number "v4"
    p3 = validate_action_parameters("APPLY_CODE_CHANGE", {
        "version_id": "v4",
        "reason": "Test change",
        "changes": [{"file_path": "App.tsx", "content": "export default function App() {}"}],
    })
    assert p3.version_id == "v4"


def create_test_service(mock_session):
    return EngineeringActionService(
        session=mock_session,
        version_service=MagicMock(),
        verification_service=MagicMock(),
        requirement_service=MagicMock(),
        context_engine=MagicMock(),
        workflow_service=MagicMock(),
    )


@pytest.mark.asyncio
async def test_resolve_version_reference_by_uuid(sample_project_id, sample_versions):
    """Verify resolution of an exact UUID reference."""
    mock_session = AsyncMock(spec=AsyncSession)
    v2 = sample_versions["v2"]

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = v2
    mock_session.execute.return_value = mock_result

    service = create_test_service(mock_session)
    resolved = await service.resolve_version_reference(sample_project_id, v2.id)

    assert resolved.id == v2.id
    assert resolved.version_number == 2


@pytest.mark.asyncio
async def test_resolve_version_reference_by_int(sample_project_id, sample_versions):
    """Verify resolution of an integer version number (e.g. 2)."""
    mock_session = AsyncMock(spec=AsyncSession)
    v2 = sample_versions["v2"]

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = v2
    mock_session.execute.return_value = mock_result

    service = create_test_service(mock_session)
    resolved = await service.resolve_version_reference(sample_project_id, 2)

    assert resolved.id == v2.id
    assert resolved.version_number == 2


@pytest.mark.asyncio
async def test_resolve_version_reference_by_string_v_prefix(sample_project_id, sample_versions):
    """Verify resolution of string version numbers like 'v2' or 'V2'."""
    mock_session = AsyncMock(spec=AsyncSession)
    v2 = sample_versions["v2"]

    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = v2
    mock_session.execute.return_value = mock_result

    service = create_test_service(mock_session)
    resolved_lower = await service.resolve_version_reference(sample_project_id, "v2")
    assert resolved_lower.id == v2.id

    resolved_upper = await service.resolve_version_reference(sample_project_id, "V2")
    assert resolved_upper.id == v2.id


@pytest.mark.asyncio
async def test_resolve_version_reference_malformed_rejected(sample_project_id):
    """Verify malformed version strings (e.g. 'invalid', 'v-1', '', 'latest') are rejected."""
    mock_session = AsyncMock(spec=AsyncSession)
    service = create_test_service(mock_session)

    with pytest.raises(ValidationError, match="Invalid version reference"):
        await service.resolve_version_reference(sample_project_id, "invalid")

    with pytest.raises(ValidationError, match="Version reference cannot be empty"):
        await service.resolve_version_reference(sample_project_id, "   ")

    with pytest.raises(ValidationError, match="Version number must be positive"):
        await service.resolve_version_reference(sample_project_id, -1)

    with pytest.raises(ValidationError, match="Version reference cannot be null"):
        await service.resolve_version_reference(sample_project_id, None)


@pytest.mark.asyncio
async def test_resolve_version_reference_not_found(sample_project_id):
    """Verify non-existent version number raises NotFoundError."""
    mock_session = AsyncMock(spec=AsyncSession)
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    service = create_test_service(mock_session)
    with pytest.raises(NotFoundError):
        await service.resolve_version_reference(sample_project_id, 999)


@pytest.mark.asyncio
async def test_resolve_version_reference_stale_rejection(sample_project_id, sample_versions):
    """Verify that targeting an inactive/superseded version raises ValidationError when require_active=True."""
    mock_session = AsyncMock(spec=AsyncSession)
    v1 = sample_versions["v1"]
    v2 = sample_versions["v2"]

    # First query returns v1 (the requested version)
    mock_res_v = MagicMock()
    mock_res_v.scalar_one_or_none.return_value = v1

    # Second query returns the project where active_version_id points to v2
    project = Project(
        id=sample_project_id,
        name="Test",
        slug="test",
        settings={"active_version_id": str(v2.id)},
    )
    mock_res_p = MagicMock()
    mock_res_p.scalar_one_or_none.return_value = project

    mock_session.execute.side_effect = [mock_res_v, mock_res_p]

    service = create_test_service(mock_session)
    with pytest.raises(ValidationError, match="is not the active version"):
        await service.resolve_version_reference(sample_project_id, 1, require_active=True)


@pytest.mark.asyncio
async def test_resolve_version_reference_cross_project_isolation(sample_project_id, other_project_id, sample_versions):
    """Verify that querying a version number from another project returns NotFoundError."""
    mock_session = AsyncMock(spec=AsyncSession)
    # The database query filters by project_id == sample_project_id.
    # Therefore, version 1 of other_project_id is not returned!
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_session.execute.return_value = mock_result

    service = create_test_service(mock_session)
    with pytest.raises(NotFoundError):
        # Even though other_project has v1, sample_project does not find it
        await service.resolve_version_reference(sample_project_id, 1)
