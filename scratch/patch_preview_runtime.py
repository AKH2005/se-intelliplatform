from pathlib import Path

# Patch backend/app/api/v1/endpoints/preview_runtime.py
pr_path = Path("backend/app/api/v1/endpoints/preview_runtime.py")
if not pr_path.exists():
    pr_path = Path("app/api/v1/endpoints/preview_runtime.py")

content = pr_path.read_text(encoding="utf-8")

# 1. Authoritative resolve_project_mode
old_resolve = '''def resolve_project_mode(project: Optional[Project], requested_mode: Optional[str] = None) -> str:
    """Determine application preview mode based on project metadata, category, and overrides."""
    valid_modes = {
        "analytics", "snake_game", "carrom", "shadow_master", "taskflow",
        "eventhub", "ecommerce", "management", "chess", "platformer",
        "racing", "puzzle", "educational", "custom",
    }
    if requested_mode and requested_mode in valid_modes:
        return requested_mode

    if not project:
        return "custom"

    p_name = project.name or ""
    p_desc = project.description or ""
    p_cat = ""
    if isinstance(project.settings, dict):
        p_arch = (project.settings.get("archetype") or "").lower()
        if p_arch in valid_modes:
            return p_arch
        p_cat = (project.settings.get("category") or "")

    from app.agents.code_generation.archetypes import detect_project_archetype
    return detect_project_archetype(p_name, p_desc, p_cat)'''

new_resolve = '''def resolve_project_mode(project: Optional[Project], requested_mode: Optional[str] = None) -> str:
    """Determine application preview mode based on project metadata, category, and overrides."""
    valid_modes = {
        "analytics", "snake_game", "carrom", "shadow_master", "taskflow",
        "eventhub", "ecommerce", "management", "chess", "platformer",
        "racing", "puzzle", "educational", "custom",
    }
    # 1. Authoritative: Project canonical settings archetype takes absolute precedence
    if project and isinstance(project.settings, dict):
        p_arch = (project.settings.get("archetype") or "").lower()
        if p_arch in valid_modes:
            return p_arch

    # 2. Requested mode (only for unconfigured projects)
    if requested_mode and requested_mode in valid_modes:
        return requested_mode

    if not project:
        return "custom"

    p_name = project.name or ""
    p_desc = project.description or ""
    p_cat = (project.settings.get("category") or "") if isinstance(project.settings, dict) else ""

    from app.agents.code_generation.archetypes import detect_project_archetype
    return detect_project_archetype(p_name, p_desc, p_cat)'''

# 2. Compute preview url without hardcoding &app= when project_id is present
old_compute = '''    if is_healthy_port_8001 and not is_prod:
        return f"http://127.0.0.1:8001/?project_id={project_id}&app={active_mode}{token_suffix}", 8001

    # Default to HTTPS-compatible FastAPI route for production Render and local development
    return f"{settings.API_V1_STR}/projects/{project_id}/runtime/preview?app={active_mode}{token_suffix}", effective_port'''

new_compute = '''    if is_healthy_port_8001 and not is_prod:
        return f"http://127.0.0.1:8001/?project_id={project_id}{token_suffix}", 8001

    # Default to HTTPS-compatible FastAPI route for production Render and local development
    return f"{settings.API_V1_STR}/projects/{project_id}/runtime/preview?{token_suffix.lstrip('&')}", effective_port'''

# 3. Defensive Shadow Master anti-collision check
old_collision = '''        # Defensive anti-collision check for generic playground files on specialized archetypes
        generic_playground_collision = False
        if mode and mode != "custom" and html_content:
            playground_markers = ["Interactive Application Playground", "Trigger Primary Action", "SE IntelliPlatform Application"]
            if any(marker in html_content for marker in playground_markers):
                generic_playground_collision = True
                logger.warning(
                    "Generic playground collision detected in files_map for project %s (mode=%s); bypassing stale generic files to serve authentic archetype prototype",
                    project_id,
                    mode,
                )

        if not legacy_kanban_collision and not legacy_snake_collision and not generic_playground_collision:'''

new_collision = '''        # Defensive anti-collision check for generic playground files on specialized archetypes
        generic_playground_collision = False
        if mode and mode != "custom" and html_content:
            playground_markers = ["Interactive Application Playground", "Trigger Primary Action", "SE IntelliPlatform Application"]
            if any(marker in html_content for marker in playground_markers):
                generic_playground_collision = True
                logger.warning(
                    "Generic playground collision detected in files_map for project %s (mode=%s); bypassing stale generic files to serve authentic archetype prototype",
                    project_id,
                    mode,
                )

        # Defensive anti-collision check for legacy Shadow Master files on non-shadow_master archetypes
        legacy_shadow_collision = False
        if mode and mode != "shadow_master" and html_content:
            shadow_collision_markers = ["combatCanvas", "Katana Slash", "Shadow Master Skill Builder", "The Shadow Master"]
            if any(marker in html_content for marker in shadow_collision_markers):
                legacy_shadow_collision = True
                logger.warning(
                    "Legacy Shadow Master collision detected in files_map for project %s (mode=%s); bypassing stale Shadow Master files",
                    project_id,
                    mode,
                )

        if not legacy_kanban_collision and not legacy_snake_collision and not generic_playground_collision and not legacy_shadow_collision:'''

# Replace patterns
for old_t, new_t in [(old_resolve, new_resolve), (old_compute, new_compute), (old_collision, new_collision)]:
    if old_t in content:
        content = content.replace(old_t, new_t, 1)
        print("Replaced LF pattern in preview_runtime.py")
    elif old_t.replace("\n", "\r\n") in content:
        content = content.replace(old_t.replace("\n", "\r\n"), new_t.replace("\n", "\r\n"), 1)
        print("Replaced CRLF pattern in preview_runtime.py")
    else:
        print("ERROR: Target pattern not found in preview_runtime.py")
        exit(1)

pr_path.write_text(content, encoding="utf-8")
print("Successfully patched preview_runtime.py!")
