"""API v1 Central Router Aggregator."""

from fastapi import APIRouter

from app.api.v1.endpoints import (
    agents,
    ai_tests,
    analysis,
    assistant,
    auth,
    browser_journeys,
    browser_testing,
    code_intelligence,
    context,
    development_versions,
    environments,
    health,
    preview_runtime,
    projects,
    remediation,
    requirements,
    sandbox,
    telemetry,
    testing,
    workflows,
)

api_v1_router = APIRouter()

api_v1_router.include_router(health.router, tags=["Health"])
api_v1_router.include_router(auth.router, prefix="/auth", tags=["Authentication"])
api_v1_router.include_router(projects.router, prefix="/projects", tags=["Projects"])
api_v1_router.include_router(
    requirements.router,
    prefix="/projects/{project_id}/requirements",
    tags=["Requirements"],
)
api_v1_router.include_router(
    context.router,
    prefix="/projects/{project_id}/context",
    tags=["Context"],
)
api_v1_router.include_router(agents.router, prefix="/agents", tags=["Agents"])
api_v1_router.include_router(workflows.router, prefix="/workflows", tags=["Workflows"])
api_v1_router.include_router(
    workflows.project_workflows_router,
    prefix="/projects/{project_id}/workflows",
    tags=["Workflows"],
)
api_v1_router.include_router(
    sandbox.router,
    prefix="/projects/{project_id}/sandbox",
    tags=["Sandbox"],
)
api_v1_router.include_router(
    analysis.router,
    prefix="/projects/{project_id}/analysis",
    tags=["Analysis"],
)
api_v1_router.include_router(
    remediation.router,
    prefix="/projects/{project_id}/remediation",
    tags=["Remediation"],
)
api_v1_router.include_router(
    ai_tests.router,
    prefix="/projects/{project_id}/tests/ai",
    tags=["AI Tests"],
)
api_v1_router.include_router(
    development_versions.router,
    prefix="/projects/{project_id}/versions",
    tags=["Development Versions"],
)
api_v1_router.include_router(
    assistant.router,
    prefix="/projects/{project_id}/assistant",
    tags=["Intelli Assistant"],
)
api_v1_router.include_router(
    browser_testing.router,
    prefix="/projects/{project_id}/browser",
    tags=["Browser Testing"],
)
api_v1_router.include_router(
    browser_journeys.router,
    prefix="/projects/{project_id}/browser-journeys",
    tags=["Browser Journeys"],
)
api_v1_router.include_router(
    testing.router,
    prefix="/projects/{project_id}/testing",
    tags=["Testing & Regression"],
)
api_v1_router.include_router(
    telemetry.router,
    prefix="/projects/{project_id}/telemetry",
    tags=["Telemetry"],
)
api_v1_router.include_router(
    environments.router,
    prefix="/projects/{project_id}/environments",
    tags=["Environments & Deployments"],
)
api_v1_router.include_router(
    code_intelligence.router,
    prefix="/projects/{project_id}/code-intelligence",
    tags=["Polyglot Code Intelligence"],
)
api_v1_router.include_router(
    preview_runtime.router,
    prefix="/projects/{project_id}/runtime",
    tags=["Application Preview Runtime"],
)






