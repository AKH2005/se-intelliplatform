"""Authoritative Deployment Target Abstraction for Phase 13.

Separates WHAT VERSION from WHERE DEPLOYED:
- AbstractDeploymentTarget defines the contract for runtime deployment targets.
- IsolatedRuntimeDeploymentAdapter implements containerized/isolated runtime deployment.
"""

import abc
from datetime import datetime, timezone
import logging
from typing import Any
import uuid
from pydantic import BaseModel, ConfigDict, Field

from app.models.development_version import DevelopmentVersion
from app.models.environment import Environment, EnvironmentType

logger = logging.getLogger(__name__)


class DeploymentExecutionResult(BaseModel):
    """Result returned by a deployment target adapter after executing deployment."""

    model_config = ConfigDict(arbitrary_types_allowed=True)

    success: bool
    status: str
    target_host: str | None = None
    target_port: int | None = None
    deployed_files_count: int = 0
    verification_passed: bool = True
    error_message: str | None = None
    details: dict[str, Any] = Field(default_factory=dict)
    completed_at: datetime = Field(default_factory=lambda: datetime.now(timezone.utc))


class AbstractDeploymentTarget(abc.ABC):
    """Abstract interface defining the execution boundary of an environment deployment target."""

    @abc.abstractmethod
    async def validate_target(
        self,
        environment: Environment,
        version: DevelopmentVersion,
    ) -> tuple[bool, str | None]:
        """Validate whether the target environment can receive the candidate version."""
        pass

    @abc.abstractmethod
    async def execute_deployment(
        self,
        environment: Environment,
        version: DevelopmentVersion,
        deployment_id: uuid.UUID,
    ) -> DeploymentExecutionResult:
        """Execute the physical or containerized deployment of the version to the target environment."""
        pass

    @abc.abstractmethod
    async def verify_health(
        self,
        environment: Environment,
    ) -> bool:
        """Verify runtime health of the deployed environment."""
        pass


class IsolatedRuntimeDeploymentAdapter(AbstractDeploymentTarget):
    """Concrete deployment adapter for SE IntelliPlatform's isolated containerized runtime."""

    def __init__(self, runtime_manager: Any | None = None) -> None:
        self.runtime_manager = runtime_manager

    async def validate_target(
        self,
        environment: Environment,
        version: DevelopmentVersion,
    ) -> tuple[bool, str | None]:
        """Validate target readiness."""
        if not version.files_manifest and version.file_count == 0:
            return False, "Cannot deploy empty version with zero files."
        if environment.status.value == "MAINTENANCE":
            return False, "Environment is currently in MAINTENANCE mode."
        return True, None

    async def execute_deployment(
        self,
        environment: Environment,
        version: DevelopmentVersion,
        deployment_id: uuid.UUID,
    ) -> DeploymentExecutionResult:
        """Simulate/execute isolated containerized deployment of the version."""
        logger.info(
            f"Executing deployment {deployment_id} to [{environment.environment_type.value}] "
            f"for version v{version.version_number} (hash={version.content_hash[:8]})."
        )
        try:
            # Deterministic simulation of deployment preparation and artifact binding
            file_count = version.file_count or len(version.files_manifest)
            target_port = 8000 + (100 if environment.environment_type == EnvironmentType.STAGING else 200 if environment.environment_type == EnvironmentType.PRODUCTION else 0)

            return DeploymentExecutionResult(
                success=True,
                status="SUCCEEDED",
                target_host=f"env-{environment.environment_type.value.lower()}.internal",
                target_port=target_port,
                deployed_files_count=file_count,
                verification_passed=True,
                details={
                    "deployment_id": str(deployment_id),
                    "environment_type": environment.environment_type.value,
                    "version_number": version.version_number,
                    "content_hash": version.content_hash,
                    "manifest_hash": version.manifest_hash,
                },
            )
        except Exception as exc:
            logger.error(f"Deployment execution failure on environment {environment.id}: {exc}", exc_info=True)
            return DeploymentExecutionResult(
                success=False,
                status="FAILED",
                error_message=str(exc),
                verification_passed=False,
            )

    async def verify_health(
        self,
        environment: Environment,
    ) -> bool:
        """Check target health."""
        return environment.status.value != "FAILED"
