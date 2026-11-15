import urllib.request
import json
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

def test_endpoints():
    print("=== TESTING PREVIEW SERVER (PORT 8001) ===")
    endpoints = {
        "/health": ["status", "ok"],
        "/chess": ["Chess Master Pro", "board"],
        "/platformer": ["Skyline Jump Platformer", "platformerCanvas"],
        "/racing": ["Turbo Nitro Racing", "raceCanvas"],
        "/puzzle": ["Tile Shift Puzzle", "grid"],
        "/educational": ["StudyDeck", "flashcard"],
        "/carrom": ["Carrom Master", "carromCanvas"],
        "/shadow_master": ["Shadow Master", "combatCanvas"],
        "/?app=custom": ["Interactive Application Dashboard", "kpi"],
    }
    
    all_passed = True
    for ep, markers in endpoints.items():
        url = f"http://127.0.0.1:8001{ep}"
        try:
            req = urllib.request.Request(url)
            with urllib.request.urlopen(req, timeout=5) as resp:
                content = resp.read().decode("utf-8", errors="replace")
                missing = [m for m in markers if m.lower() not in content.lower()]
                if not missing:
                    print(f"PASS: {ep} -> HTTP {resp.status} with expected markers {markers}")
                else:
                    print(f"FAIL: {ep} -> Missing markers: {missing}")
                    all_passed = False
        except Exception as e:
            print(f"ERROR: {ep} -> {e}")
            all_passed = False

    print("\n=== TESTING ARCHETYPE CODE GENERATORS ===")
    from app.agents.code_generation.archetypes import (
        ARCHETYPE_TEMPLATES,
        detect_project_archetype,
        get_archetype_planned_files,
        get_archetype_file_content,
    )
    from app.services.development_version_service import FileValidator, ApplicationIntegrityValidator

    print(f"Total Archetypes Registered: {len(ARCHETYPE_TEMPLATES)}")
    for arch_key in ARCHETYPE_TEMPLATES:
        planned = get_archetype_planned_files(arch_key)
        print(f"Archetype '{arch_key}': {len(planned)} planned files")
        if len(planned) < 10:
            print(f"FAIL: {arch_key} has only {len(planned)} files")
            all_passed = False

        # Validate generated files
        files_to_check = []
        for p in planned[:5]:  # sample check
            content = get_archetype_file_content(arch_key, p.get("path", ""))
            files_to_check.append({"path": p.get("path", ""), "content": content})
            val = FileValidator.validate(p.get("path", ""), content)
            if val.status != "PASSED":
                print(f"FAIL: Validation error in {arch_key} file {p.get('path')}: {val.message}")
                all_passed = False

        ok, errs = ApplicationIntegrityValidator.validate_package(files_to_check, archetype=arch_key)
        if not ok:
            print(f"FAIL: ApplicationIntegrityValidator for {arch_key}: {errs}")
            all_passed = False

    if all_passed:
        print("\nALL PREVIEW SERVER & ARCHETYPE CHECKS PASSED 100%!")
    else:
        print("\nSOME CHECKS FAILED!")
        sys.exit(1)

if __name__ == "__main__":
    test_endpoints()
