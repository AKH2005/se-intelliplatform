import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.agents.code_generation.archetypes import get_archetype_planned_files, get_archetype_file_content
from app.services.development_version_service import FileValidator

def test_all_files():
    files = get_archetype_planned_files("shadow_master")
    print(f"Total planned files: {len(files)}")
    for f in files:
        print("  -", f["path"])

    for f in files:
        p = f["path"]
        content = get_archetype_file_content(
            "shadow_master",
            p,
            project_name="Shadow Master Skill Builder",
            project_desc="A web-based tool that lets game designers create, preview, and export custom skills for the Shadow Master game."
        )
        assert content is not None, f"Content for {p} is None!"
        assert len(content) > 20, f"Content for {p} is too short ({len(content)})"

        # Validate with FileValidator
        outcome = FileValidator.validate(p, content)
        print(f"[{outcome.status}] {p} ({len(content)} bytes)")
        if outcome.status == "FAILED":
            print(f"  FAILED DETAILS: {outcome.errors}")
            raise ValueError(f"Validation failed for {p}")

    print("\nALL 15 SHADOW MASTER FILES PASSED FILEVALIDATOR 100%!")

if __name__ == "__main__":
    test_all_files()
