"""Deterministic Validation and Security Guardrails for Remediation Proposals."""

import logging
import re
from typing import Any
from app.agents.contracts import ValidationResult
from app.agents.remediation.contracts import (
    ChangeOperation,
    ProposedChange,
    RemediationProposalCandidate,
    RemediationProposalInput,
)

logger = logging.getLogger(__name__)


class RemediationProposalValidator:
    """Strictly validates RemediationProposalCandidate against deterministic constraints and safety limits."""

    # Deterministic Bounds
    MAX_CHANGED_FILES: int = 5
    MAX_ADDED_BYTES: int = 50 * 1024       # 50 KB
    MAX_DELETED_BYTES: int = 50 * 1024     # 50 KB
    MAX_TOTAL_PATCH_SIZE: int = 100 * 1024 # 100 KB
    MAX_INDIVIDUAL_FILE_SIZE: int = 100 * 1024 # 100 KB

    # Forbidden files & directory patterns
    FORBIDDEN_FILE_PATTERNS = [
        re.compile(r"(^|/)\.env($|\..*)"),
        re.compile(r"(^|/)\.git/"),
        re.compile(r"(^|/)\.github/"),
        re.compile(r"(^|/)Dockerfile.*"),
        re.compile(r"(^|/)docker-compose.*"),
        re.compile(r"/var/run/docker\.sock"),
        re.compile(r"(^|/)\.bash_.*"),
        re.compile(r"(^|/)\.ssh/"),
    ]

    # Secret scanning patterns
    SECRET_PATTERNS = [
        re.compile(r"-----BEGIN (?:RSA |EC |OPENSSH |DSA )?PRIVATE KEY-----"),
        re.compile(r"(?:api[_-]?key|secret[_-]?key|access[_-]?token)\s*[:=]\s*['\"][A-Za-z0-9_\-]{16,}['\"]", re.IGNORECASE),
        re.compile(r"AKIA[0-9A-Z]{16}"),  # AWS Access Key ID
        re.compile(r"eyJ[A-Za-z0-9_-]{10,}\.eyJ[A-Za-z0-9_-]{10,}\.[A-Za-z0-9_-]{10,}"),  # JWT
        re.compile(r"ghp_[A-Za-z0-9]{36}"),  # GitHub Personal Access Token
    ]

    @classmethod
    def validate(
        cls,
        candidate: RemediationProposalCandidate,
        analysis_input: RemediationProposalInput,
        current_files: dict[str, str] | None = None,
    ) -> ValidationResult:
        errors: list[str] = []

        valid_manifest = set(analysis_input.project_manifest)
        valid_req_ids = set(analysis_input.available_requirement_ids)
        valid_arch_components = set(analysis_input.available_architecture_components)
        valid_db_entities = set(analysis_input.available_database_entities)

        # 1. Bounded Changed Files
        if len(candidate.changes) > cls.MAX_CHANGED_FILES:
            errors.append(
                f"Proposal exceeds maximum changed files limit: {len(candidate.changes)} > {cls.MAX_CHANGED_FILES}."
            )

        seen_files: set[str] = set()
        total_added_bytes = 0
        total_deleted_bytes = 0

        for idx, change in enumerate(candidate.changes):
            change_id = f"Change #{idx + 1}"
            raw_path = change.file_path

            # 2. Path Safety Checks
            if not raw_path or not raw_path.strip():
                errors.append(f"{change_id}: file_path cannot be empty.")
                continue

            if "\\" in raw_path:
                errors.append(f"{change_id} contains backslashes in path '{raw_path}'. Only forward slashes are permitted.")

            clean_path = raw_path.replace("\\", "/").strip()

            if clean_path.startswith("/"):
                errors.append(f"{change_id} path '{raw_path}' is absolute. Only project-relative paths are permitted.")

            if len(clean_path) >= 2 and clean_path[1] == ":":
                errors.append(f"{change_id} path '{raw_path}' contains Windows drive letter. Only relative paths are permitted.")

            parts = clean_path.split("/")
            if ".." in parts or "." in parts[:-1]:
                errors.append(f"{change_id} path '{raw_path}' contains forbidden directory traversal ('..').")

            for fpat in cls.FORBIDDEN_FILE_PATTERNS:
                if fpat.search(clean_path):
                    errors.append(f"{change_id} attempts to access forbidden path '{raw_path}'.")

            # 3. Duplicate Operation Check
            if clean_path in seen_files:
                errors.append(f"{change_id} duplicate modification on file '{clean_path}' in the same proposal.")
            seen_files.add(clean_path)

            # 4. Manifest Existence
            if change.operation in (ChangeOperation.MODIFY, ChangeOperation.DELETE):
                if clean_path not in valid_manifest:
                    errors.append(
                        f"{change_id} ({change.operation.value}): Target file '{clean_path}' does not exist in project manifest."
                    )
            elif change.operation == ChangeOperation.ADD:
                if clean_path in valid_manifest:
                    errors.append(
                        f"{change_id} (ADD): File '{clean_path}' already exists in project manifest. Use MODIFY instead."
                    )

            # 5. Patch Size Bounds
            added_b = len(change.proposed_region.encode("utf-8")) if change.proposed_region else 0
            deleted_b = len(change.original_region.encode("utf-8")) if change.original_region else 0

            total_added_bytes += added_b
            total_deleted_bytes += deleted_b

            if added_b > cls.MAX_INDIVIDUAL_FILE_SIZE:
                errors.append(
                    f"{change_id} proposed content exceeds individual file size limit ({added_b} > {cls.MAX_INDIVIDUAL_FILE_SIZE} bytes)."
                )

            # 6. Content Applicability (if current_files supplied)
            if current_files is not None and change.operation == ChangeOperation.MODIFY:
                if clean_path in current_files and change.original_region:
                    norm_curr = current_files[clean_path].replace("\r\n", "\n")
                    norm_orig = change.original_region.replace("\r\n", "\n")
                    if norm_orig not in norm_curr:
                        errors.append(
                            f"{change_id} original_region does not match current content of '{clean_path}'."
                        )

            # 7. Secret Scanning
            if change.proposed_region:
                for spat in cls.SECRET_PATTERNS:
                    if spat.search(change.proposed_region):
                        errors.append(
                            f"{change_id} contains detected secret pattern in proposed_region. Rejecting proposal for security."
                        )
                        break

        # Check total limits
        if total_added_bytes > cls.MAX_ADDED_BYTES:
            errors.append(f"Total added bytes ({total_added_bytes}) exceeds maximum allowed ({cls.MAX_ADDED_BYTES}).")
        if total_deleted_bytes > cls.MAX_DELETED_BYTES:
            errors.append(f"Total deleted bytes ({total_deleted_bytes}) exceeds maximum allowed ({cls.MAX_DELETED_BYTES}).")
        if (total_added_bytes + total_deleted_bytes) > cls.MAX_TOTAL_PATCH_SIZE:
            errors.append(f"Total patch size exceeds maximum allowed ({cls.MAX_TOTAL_PATCH_SIZE} bytes).")

        # 8. Traceability Link Checks
        for req_id in candidate.requirement_links:
            clean_req = req_id.strip()
            if clean_req not in valid_req_ids:
                errors.append(
                    f"Hallucinated requirement link '{req_id}': Requirement ID does not exist in project context."
                )

        for comp_name in candidate.architecture_links:
            clean_comp = comp_name.strip()
            if clean_comp not in valid_arch_components:
                errors.append(
                    f"Hallucinated architecture link '{comp_name}': Component does not exist in architecture context."
                )

        for entity_name in candidate.database_links:
            clean_entity = entity_name.strip()
            if clean_entity not in valid_db_entities:
                errors.append(
                    f"Hallucinated database link '{entity_name}': Entity does not exist in database context."
                )

        if errors:
            logger.warning(f"RemediationProposal validation failed with {len(errors)} error(s): {errors}")
            return ValidationResult(is_valid=False, errors=errors)

        return ValidationResult(is_valid=True)
