"""Deterministic Unified Diff Generator for Remediation Proposals."""

import difflib
from app.agents.remediation.contracts import ChangeOperation, ProposedChange


class DiffGenerator:
    """Generates deterministic, audit-grade unified diffs for proposed changes."""

    @classmethod
    def apply_changes_to_files(
        cls,
        current_files: dict[str, str],
        changes: list[ProposedChange],
    ) -> tuple[str, dict[str, str]]:
        """Apply structured changes to a copy of file dictionary and compute unified diff.

        Returns:
            (unified_diff_text, modified_files_dict)

        Raises:
            ValueError if a MODIFY change cannot find its original_region.
        """
        updated_files = dict(current_files)
        diff_chunks: list[str] = []

        for change in changes:
            path = change.file_path.replace("\\", "/").strip()

            if change.operation == ChangeOperation.ADD:
                original_content = ""
                new_content = change.proposed_region
                updated_files[path] = new_content

                original_lines = []
                new_lines = new_content.splitlines(keepends=True)
                if new_lines and not new_lines[-1].endswith("\n"):
                    new_lines[-1] += "\n"

                hunks = list(
                    difflib.unified_diff(
                        original_lines,
                        new_lines,
                        fromfile=f"/dev/null",
                        tofile=f"b/{path}",
                    )
                )
                if hunks:
                    diff_chunks.append("".join(hunks))

            elif change.operation == ChangeOperation.DELETE:
                if path not in updated_files:
                    raise ValueError(f"Cannot delete non-existent file '{path}'.")
                original_content = updated_files[path]
                del updated_files[path]

                original_lines = original_content.splitlines(keepends=True)
                if original_lines and not original_lines[-1].endswith("\n"):
                    original_lines[-1] += "\n"

                hunks = list(
                    difflib.unified_diff(
                        original_lines,
                        [],
                        fromfile=f"a/{path}",
                        tofile=f"/dev/null",
                    )
                )
                if hunks:
                    diff_chunks.append("".join(hunks))

            elif change.operation == ChangeOperation.MODIFY:
                if path not in updated_files:
                    raise ValueError(f"Cannot modify non-existent file '{path}'.")
                original_content = updated_files[path]

                if change.original_region:
                    # Clean CRLF differences if any
                    norm_orig = original_content.replace("\r\n", "\n")
                    norm_region = change.original_region.replace("\r\n", "\n")
                    if norm_region not in norm_orig:
                        raise ValueError(
                            f"Proposed change for '{path}' failed: specified original_region was not found in the file."
                        )
                    # Replace only first occurrence
                    new_content = norm_orig.replace(norm_region, change.proposed_region.replace("\r\n", "\n"), 1)
                else:
                    new_content = change.proposed_region

                updated_files[path] = new_content

                original_lines = original_content.splitlines(keepends=True)
                if original_lines and not original_lines[-1].endswith("\n"):
                    original_lines[-1] += "\n"

                new_lines = new_content.splitlines(keepends=True)
                if new_lines and not new_lines[-1].endswith("\n"):
                    new_lines[-1] += "\n"

                hunks = list(
                    difflib.unified_diff(
                        original_lines,
                        new_lines,
                        fromfile=f"a/{path}",
                        tofile=f"b/{path}",
                    )
                )
                if hunks:
                    diff_chunks.append("".join(hunks))

        full_diff = "\n".join(diff_chunks).strip()
        return full_diff, updated_files
