"""
Add ApplicationIntegrityValidator to backend/app/services/development_version_service.py
"""
import ast
import re
from pathlib import Path

target_file = Path("backend/app/services/development_version_service.py")
content = target_file.read_text(encoding="utf-8")

if "class ApplicationIntegrityValidator:" in content:
    print("ApplicationIntegrityValidator already exists.")
else:
    validator_code = '''
class ApplicationIntegrityValidator:
    """Deterministic validation of application package integrity and archetype conformity."""

    @classmethod
    def validate_package(
        cls,
        files: list[Any],
        archetype: Optional[str] = None,
        project_name: str = "",
    ) -> tuple[bool, list[str]]:
        """Validate package integrity, entry points, non-stub content, and archetype anti-collision."""
        errors: list[str] = []
        paths = [f.path if hasattr(f, "path") else f.get("path", "") for f in files]

        # 1. Entry point check: full apps should have an HTML entry point
        has_html_entry = any(
            p in ("frontend/index.html", "index.html", "public/index.html") or p.endswith(".html")
            for p in paths
        )
        if not has_html_entry and len(files) > 1:
            errors.append("Package is missing frontend entry point (index.html or frontend/index.html).")

        # 2. Empty / stub check
        for f in files:
            path = f.path if hasattr(f, "path") else f.get("path", "")
            content = f.content if hasattr(f, "content") else f.get("content", "")
            if not path.endswith("__init__.py"):
                stripped = (content or "").strip()
                if len(stripped) < 15:
                    errors.append(f"File '{path}' appears to be an empty stub ({len(stripped)} chars).")
                elif stripped in ("def init_module(): pass", "pass", "# Stub", "// Stub"):
                    errors.append(f"File '{path}' contains placeholder stub code.")

        # 3. Archetype Anti-Collision Check
        if archetype and archetype not in ("taskflow", "custom"):
            for f in files:
                content = f.content if hasattr(f, "content") else f.get("content", "")
                if any(m in content for m in ["new-task-input", "loadTasks()", "KanbanFlow Board"]):
                    errors.append(f"Archetype collision: File contains Kanban TaskFlow markers in non-taskflow project ({archetype}).")
                    break

        if archetype and archetype != "snake_game":
            for f in files:
                content = f.content if hasattr(f, "content") else f.get("content", "")
                if any(m in content for m in ["spawnFood()", "snake_high_score", "Arcade Snake"]):
                    errors.append(f"Archetype collision: File contains Snake markers in non-snake project ({archetype}).")
                    break

        return (len(errors) == 0, errors)
'''

    # Place right after FileValidator
    target_idx = content.find("class FileValidator:")
    if target_idx == -1:
        raise ValueError("Could not find class FileValidator in development_version_service.py")

    # Find the end of FileValidator (build_file_tree)
    tree_idx = content.find("def build_file_tree(", target_idx)
    if tree_idx == -1:
        raise ValueError("Could not find def build_file_tree")

    content = content[:tree_idx] + validator_code + "\n\n" + content[tree_idx:]
    
    ast.parse(content, filename="development_version_service.py")
    target_file.write_text(content, encoding="utf-8")
    print("Added ApplicationIntegrityValidator and AST validated successfully!")

