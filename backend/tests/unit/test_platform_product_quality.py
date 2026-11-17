"""Unit and Regression Tests for Platform-Wide Product Quality Upgrade.

Tests:
1. Space Arcade Archetype Separation (Verify Arcade != Snake)
2. Application Integrity Validator stub & placeholder detection
3. Anti-collision identity checks
4. Extended Quality Gates (Identity, Workflows/Routes, Authentication)
5. Archetype planned file manifests and code content generation
"""

import pytest
from app.agents.code_generation.archetypes import (
    get_archetype_planned_files,
    get_archetype_file_content,
    detect_project_archetype,
)
from app.services.development_version_service import ApplicationIntegrityValidator
from app.agents.code_generation.quality_gates import (
    evaluate_identity_correctness_gate,
    evaluate_workflow_and_route_integrity_gate,
    evaluate_authentication_integrity_gate,
)


class TestArchetypeSeparation:
    """Test that general arcade requests do not substitute Snake."""

    def test_detect_space_arcade(self):
        arch = detect_project_archetype(name="Galactic Strike", desc="A high-octane 2D space shooter arcade game with lasers and alien waves")
        assert arch == "space_arcade"
        assert arch != "snake_game"

    def test_detect_snake_only_when_explicit(self):
        arch = detect_project_archetype(name="Snake Eater", desc="A retro classic snake game with apples and growing tail")
        assert arch == "snake_game"

    def test_space_arcade_manifest(self):
        files = get_archetype_planned_files("space_arcade", "Space Defender")
        assert len(files) >= 5
        paths = [f["path"] for f in files]
        assert "frontend/index.html" in paths
        assert "frontend/src/components/ArcadeCanvas.tsx" in paths

    def test_space_arcade_content_has_no_snake(self):
        html = get_archetype_file_content("space_arcade", "frontend/index.html", "Space Defender", "Arcade Game")
        assert html is not None
        assert "Snake" not in html
        assert "canvas" in html.lower()
        assert "space arcade" in html.lower() or "defender" in html.lower()

    def test_inventory_manifest_and_content(self):
        files = get_archetype_planned_files("inventory", "Warehouse Manager")
        assert len(files) >= 5
        html = get_archetype_file_content("inventory", "frontend/index.html", "Warehouse Manager", "SKU system")
        assert html is not None
        assert "SKU" in html or "Inventory" in html

    def test_lms_manifest_and_content(self):
        files = get_archetype_planned_files("lms", "SkillForge LMS")
        assert len(files) >= 5
        html = get_archetype_file_content("lms", "frontend/index.html", "SkillForge LMS", "Course portal")
        assert html is not None
        assert "Course" in html or "Curriculum" in html


class TestApplicationIntegrityValidator:
    """Test strict stub and anti-collision validation."""

    def test_validator_rejects_empty_files(self):
        files = [{"path": "frontend/index.html", "content": ""}]
        is_valid, errors = ApplicationIntegrityValidator.validate_package(files=files, project_name="Test App", archetype="custom")
        assert not is_valid
        assert any("empty" in e.lower() for e in errors)

    def test_validator_rejects_pass_stubs(self):
        files = [
            {"path": "frontend/index.html", "content": "<!DOCTYPE html><html><body><h1>Test App</h1><div id='app'>Real Content</div></body></html>"},
            {"path": "backend/main.py", "content": "def init_module() -> None:\n    pass\n"},
        ]
        is_valid, errors = ApplicationIntegrityValidator.validate_package(files=files, project_name="Test App", archetype="custom")
        assert not is_valid
        assert any("stub" in e.lower() or "pass" in e.lower() for e in errors)

    def test_validator_rejects_shadow_warrior_collision(self):
        files = [
            {"path": "frontend/index.html", "content": "<!DOCTYPE html><html><body><h1>Shadow Warrior Skill Builder</h1></body></html>"},
        ]
        is_valid, errors = ApplicationIntegrityValidator.validate_package(files=files, project_name="Space Combat Simulator", archetype="space_arcade")
        assert not is_valid
        assert any("collision" in e.lower() or "identity" in e.lower() for e in errors)

    def test_validator_passes_complete_application(self):
        files = [
            {"path": "frontend/index.html", "content": "<!DOCTYPE html><html><body><h1>Space Combat Simulator</h1><canvas id='c'></canvas></body></html>"},
            {"path": "frontend/src/game.js", "content": "function gameLoop() { window.requestAnimationFrame(gameLoop); }\nwindow.onload = gameLoop;"},
        ]
        is_valid, errors = ApplicationIntegrityValidator.validate_package(files=files, project_name="Space Combat Simulator", archetype="space_arcade")
        assert is_valid
        assert len(errors) == 0


class TestExtendedQualityGates:
    """Test the upgraded 9-gate quality suite."""

    def test_identity_correctness_gate_passes_clean_code(self):
        files = [
            {"path": "frontend/index.html", "content": "<html><head><title>Sky Strike Dogfight</title></head><body><h1>Sky Strike Dogfight</h1></body></html>"},
        ]
        gate = evaluate_identity_correctness_gate("Sky Strike Dogfight", "sky_strike", files)
        assert gate.passed
        assert gate.score >= 80.0

    def test_identity_correctness_gate_flags_shadow_master_leak(self):
        files = [
            {"path": "frontend/index.html", "content": "<html><head><title>Shadow Master Skill Builder</title></head><body><h1>CombatCanvas Katana Slash</h1></body></html>"},
        ]
        gate = evaluate_identity_correctness_gate("Sky Strike Dogfight", "sky_strike", files)
        assert not gate.passed
        assert any("collision" in f.lower() or "shadow" in f.lower() for f in gate.checks_failed)

    def test_workflow_route_integrity_gate(self):
        files = [
            {"path": "frontend/index.html", "content": "<div class='tab-nav'><button onclick='switchTab(\"stock\")'>Stock</button></div><form onsubmit='handleStock(event)'><input id='qty'/><button type='submit' onclick='submitForm()'>Adjust</button></form><div class='alert toast'>Success</div>"},
        ]
        gate = evaluate_workflow_and_route_integrity_gate(files, is_game=False)
        assert gate.passed
        assert gate.score >= 75.0

    def test_authentication_integrity_gate_with_auth(self):
        files = [
            {"path": "frontend/index.html", "content": "<div id='authModal'><form id='loginForm'><input type='password' id='pwd'/><button id='btnLogin' onclick='submitLogin()'>Login</button></form></div><button id='btnLogout' onclick='logout()'>Logout</button><script>localStorage.getItem('token'); fetch('/api/auth/login');</script>"},
            {"path": "backend/auth.py", "content": "def hash_password(p): return 'hashed'\ndef verify_token(t): return True"},
        ]
        gate = evaluate_authentication_integrity_gate(files, auth_required=True)
        assert gate.passed
        assert gate.score >= 75.0
