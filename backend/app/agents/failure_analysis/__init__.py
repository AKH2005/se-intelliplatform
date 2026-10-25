"""Failure Analysis Agent Module."""

from app.agents.failure_analysis.agent import FailureAnalysisAgent
from app.agents.failure_analysis.contracts import (
    ClaimType,
    DiagnosticClaim,
    EvidenceReference,
    FailureAnalysisInput,
    FailureConfidence,
    FailureDiagnosis,
    FailureType,
    RelevantSourceFile,
)

from app.agents.failure_analysis.sanitizer import (
    normalize_browser_evidence,
    redact_secrets,
)

__all__ = [
    "FailureAnalysisAgent",
    "FailureAnalysisInput",
    "FailureDiagnosis",
    "FailureType",
    "ClaimType",
    "FailureConfidence",
    "EvidenceReference",
    "DiagnosticClaim",
    "RelevantSourceFile",
    "redact_secrets",
    "normalize_browser_evidence",
]
