"""REST API Endpoints for Polyglot Code Intelligence (Phase 14)."""

import logging
from typing import Any
import uuid
from fastapi import APIRouter, Depends, HTTPException, Path, Query, status
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.api.dependencies import get_current_user_optional, get_db, get_development_version_service
from app.code_intelligence.contracts import CodeLanguage
from app.code_intelligence.detector import LanguageDetector, TechnologyDetector
from app.code_intelligence.service import PolyglotCodeIntelligenceService
from app.core.exceptions import ForbiddenError, NotFoundError, UnauthorizedError
from app.models.development_version import DevelopmentVersion
from app.models.project import Project
from app.models.user import User
from app.schemas.code_intelligence import (
    CodeIntelligenceSummaryResponse,
    DependencyGraphResponse,
    FileCodeIntelligenceResponse,
    LanguageInventoryResponse,
    ProjectTechnologiesResponse,
)
from app.services.development_version_service import DevelopmentVersionService

logger = logging.getLogger(__name__)

router = APIRouter()

# Singleton code intelligence service instance
_code_intelligence_service = PolyglotCodeIntelligenceService()


def _get_code_intelligence_service() -> PolyglotCodeIntelligenceService:
    return _code_intelligence_service


async def _resolve_version_files_map(
    project_id: uuid.UUID,
    version_id: uuid.UUID | None,
    session: AsyncSession,
    version_service: DevelopmentVersionService,
    user: User | None = None,
) -> tuple[DevelopmentVersion | None, dict[str, str]]:
    """Helper to extract files_map from specified or active version, ensuring project isolation."""
    # Validate project exists and user has authorization
    p_stmt = select(Project).where(Project.id == project_id)
    p_res = await session.execute(p_stmt)
    proj = p_res.scalar_one_or_none()
    if not proj:
        raise NotFoundError("Project", str(project_id))

    if proj.owner_id is not None:
        if user is None:
            raise UnauthorizedError("Authentication required to access this project's code intelligence")
        if proj.owner_id != user.id:
            raise ForbiddenError("You do not have permission to access this project")

    version: DevelopmentVersion | None = None
    if version_id:
        v_stmt = select(DevelopmentVersion).where(
            DevelopmentVersion.id == version_id,
            DevelopmentVersion.project_id == project_id,
        )
        v_res = await session.execute(v_stmt)
        version = v_res.scalar_one_or_none()
        if not version:
            raise NotFoundError("DevelopmentVersion", str(version_id))
    else:
        active_resp = await version_service.get_active_version(project_id)
        if active_resp:
            v_stmt = select(DevelopmentVersion).where(
                DevelopmentVersion.id == active_resp.version_id,
                DevelopmentVersion.project_id == project_id,
            )
            v_res = await session.execute(v_stmt)
            version = v_res.scalar_one_or_none()

        if not version:
            latest_stmt = (
                select(DevelopmentVersion)
                .where(DevelopmentVersion.project_id == project_id)
                .order_by(DevelopmentVersion.version_number.desc())
                .limit(1)
            )
            l_res = await session.execute(latest_stmt)
            version = l_res.scalar_one_or_none()

    files_map: dict[str, str] = {}
    if version:
        try:
            files_map = await version_service._resolve_version_files_map(version)
        except Exception as e:
            logger.debug(f"Could not load artifact files for version {version.id}: {e}")

    return version, files_map


@router.get(
    "/languages",
    response_model=LanguageInventoryResponse,
    summary="Get project language inventory",
)
async def get_language_inventory(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    version_id: uuid.UUID | None = Query(None, description="Optional version UUID"),
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    service: PolyglotCodeIntelligenceService = Depends(_get_code_intelligence_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> LanguageInventoryResponse:
    """Retrieve language distribution breakdown across project source files."""
    _, files_map = await _resolve_version_files_map(project_id, version_id, session, version_service, current_user)
    breakdown = service.get_language_breakdown(files_map)

    return LanguageInventoryResponse(
        project_id=project_id,
        total_files=breakdown["total_files"],
        counts=breakdown["counts"],
        percentages=breakdown["percentages"],
        supported_languages=breakdown["supported_languages"],
    )


@router.get(
    "/technologies",
    response_model=ProjectTechnologiesResponse,
    summary="Get detected project technologies and capabilities",
)
async def get_project_technologies(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    version_id: uuid.UUID | None = Query(None, description="Optional version UUID"),
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> ProjectTechnologiesResponse:
    """Retrieve detected programming languages, web technologies, frameworks, and databases."""
    _, files_map = await _resolve_version_files_map(project_id, version_id, session, version_service, current_user)
    technologies = TechnologyDetector.detect_project_technologies(files_map)

    return ProjectTechnologiesResponse(
        project_id=project_id,
        technologies=technologies,
    )


@router.get(
    "/summary",
    response_model=CodeIntelligenceSummaryResponse,
    summary="Get code intelligence summary",
)
async def get_code_intelligence_summary(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    version_id: uuid.UUID | None = Query(None, description="Optional version UUID"),
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    service: PolyglotCodeIntelligenceService = Depends(_get_code_intelligence_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> CodeIntelligenceSummaryResponse:
    """Retrieve high-level metrics of polyglot code symbols, edges, and diagnostics."""
    version, files_map = await _resolve_version_files_map(project_id, version_id, session, version_service, current_user)
    graph = service.build_project_graph(project_id, files_map)

    return CodeIntelligenceSummaryResponse(
        project_id=project_id,
        version_id=version.id if version else None,
        version_number=version.version_number if version else None,
        total_files=len(graph.files),
        total_symbols=graph.total_symbols,
        total_edges=len(graph.edges),
        total_diagnostics=len(graph.diagnostics),
        language_breakdown=graph.language_breakdown,
        unresolved_imports_count=len(graph.unresolved_imports),
        uncertain_dependencies_count=len(graph.uncertain_dependencies),
        analyzed_at=graph.analyzed_at,
    )


@router.get(
    "/graph",
    response_model=DependencyGraphResponse,
    summary="Get polyglot dependency graph",
)
async def get_dependency_graph(
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    version_id: uuid.UUID | None = Query(None, description="Optional version UUID"),
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    service: PolyglotCodeIntelligenceService = Depends(_get_code_intelligence_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> DependencyGraphResponse:
    """Retrieve full dependency graph with forward/reverse adjacency indexing."""
    _, files_map = await _resolve_version_files_map(project_id, version_id, session, version_service, current_user)
    graph = service.build_project_graph(project_id, files_map)

    return DependencyGraphResponse(
        project_id=project_id,
        files_count=len(graph.files),
        edges_count=len(graph.edges),
        forward_adjacency=graph.forward_adjacency,
        reverse_adjacency=graph.reverse_adjacency,
        language_breakdown=graph.language_breakdown,
        unresolved_imports=graph.unresolved_imports,
        uncertain_dependencies=graph.uncertain_dependencies,
        diagnostics_count=len(graph.diagnostics),
    )


@router.get(
    "/file",
    response_model=FileCodeIntelligenceResponse,
    summary="Get single file code intelligence",
)
async def get_file_code_intelligence(
    file_path: str = Query(..., description="Project-relative file path"),
    project_id: uuid.UUID = Path(..., description="Project UUID"),
    version_id: uuid.UUID | None = Query(None, description="Optional version UUID"),
    session: AsyncSession = Depends(get_db),
    version_service: DevelopmentVersionService = Depends(get_development_version_service),
    service: PolyglotCodeIntelligenceService = Depends(_get_code_intelligence_service),
    current_user: User | None = Depends(get_current_user_optional),
) -> FileCodeIntelligenceResponse:
    """Retrieve symbols, imports, exports, and diagnostics for a specific project file."""
    _, files_map = await _resolve_version_files_map(project_id, version_id, session, version_service, current_user)
    norm_path = file_path.replace("\\", "/").strip("/")

    if norm_path not in files_map:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"File '{norm_path}' not found in project version.",
        )

    code_file = service.analyze_file(norm_path, files_map[norm_path])

    return FileCodeIntelligenceResponse(
        file_path=code_file.file_path,
        language=code_file.language,
        is_test_file=code_file.is_test_file,
        content_hash=code_file.content_hash,
        symbols=code_file.symbols,
        imports=code_file.imports,
        exports=code_file.exports,
        dependencies=code_file.dependencies,
        diagnostics=code_file.diagnostics,
        has_syntax_error=code_file.has_syntax_error,
        has_dynamic_constructs=code_file.has_dynamic_constructs,
    )
