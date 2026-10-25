"""Exception types for Unified Test Inventory & Traceability Foundation."""


class UnifiedTestInventoryError(Exception):
    """Base exception for Unified Test Inventory domain."""
    pass


class UnifiedTestInventoryConflictError(UnifiedTestInventoryError):
    """Raised when duplicate deterministic test IDs collide in strict discovery mode."""
    pass


class UnifiedTestInventoryIsolationError(UnifiedTestInventoryError):
    """Raised when test artifacts or suites violate project ownership boundaries."""
    pass


class UnifiedTestInventoryValidationError(UnifiedTestInventoryError):
    """Raised when an unvalidated candidate suite or invalid test definition is supplied."""
    pass
