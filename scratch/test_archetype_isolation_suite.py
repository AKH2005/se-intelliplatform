import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.agents.code_generation.archetypes import get_archetype_planned_files, get_archetype_file_content, classify_application_category
from app.services.development_version_service import FileValidator

def test_archetype_isolation():
    archetypes = ["shadow_master", "carrom", "analytics", "snake_game", "taskflow", "ecommerce", "management"]

    for arch in archetypes:
        planned = get_archetype_planned_files(arch)
        assert len(planned) >= 12, f"Archetype {arch} has only {len(planned)} files!"
        print(f"PASS: {arch} planned {len(planned)} files.")

        # Test index.html
        html = get_archetype_file_content(arch, "frontend/index.html", f"Test {arch}", "Test description")
        assert html is not None and len(html) > 500, f"HTML for {arch} is invalid!"

        if arch == "shadow_master":
            assert "Katana Slash" in html
            assert "Interactive Application Playground" not in html
        elif arch == "carrom":
            assert "striker" in html.lower()
        elif arch == "analytics":
            assert "MRR" in html or "Revenue" in html
        elif arch == "snake_game":
            assert "snake" in html.lower()

        # Validate index.html with FileValidator
        outcome = FileValidator.validate("frontend/index.html", html)
        assert outcome.status == "PASSED", f"FileValidator failed on {arch} index.html: {outcome.errors}"

    print("\nALL ARCHETYPES PASSED ISOLATION AND VALIDATION CHECKS 100%!")

if __name__ == "__main__":
    test_archetype_isolation()

