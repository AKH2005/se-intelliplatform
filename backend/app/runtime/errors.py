"""Exception hierarchies for Application Runtime subsystem (Phase 11J - Stage 2)."""


class RuntimeErrorBase(Exception):
    """Base exception for application runtime errors."""


class RuntimeConfigurationError(RuntimeErrorBase):
    """Raised when runtime manifest or configuration fails validation."""


class RuntimeResourceLimitError(RuntimeErrorBase):
    """Raised when concurrency, CPU, memory, or PID limits are violated."""


class RuntimeStartupError(RuntimeErrorBase):
    """Raised when application container fails during startup or exits prematurely."""


class RuntimeTimeoutError(RuntimeErrorBase):
    """Raised when application boot or total session duration exceeds timeout limit."""


class DockerUnavailableError(RuntimeErrorBase):
    """Raised when Docker daemon is unreachable or unavailable."""


class RuntimeIsolationError(RuntimeErrorBase):
    """Raised when isolation boundaries (filesystem, network, user) are compromised."""


class HealthCheckError(RuntimeErrorBase):
    """Raised when application fails internal readiness health check."""
