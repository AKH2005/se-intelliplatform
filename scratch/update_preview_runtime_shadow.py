import os
import ast

def main():
    path = r"backend\app\api\v1\endpoints\preview_runtime.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update imports
    target_import = """from app.runtime.preview_server import (
    EVENTHUB_HTML,
    get_analytics_dashboard_html,
    get_carrom_game_html,
    get_custom_app_html,"""

    replacement_import = """from app.runtime.preview_server import (
    EVENTHUB_HTML,
    get_analytics_dashboard_html,
    get_carrom_game_html,
    get_shadow_master_game_html,
    get_custom_app_html,"""

    assert target_import in content, "target_import not found"
    content = content.replace(target_import, replacement_import, 1)

    # 2. Update valid_modes
    target_modes = 'valid_modes = {"analytics", "snake_game", "carrom", "taskflow", "eventhub", "ecommerce", "management", "custom"}'
    replacement_modes = 'valid_modes = {"analytics", "snake_game", "carrom", "shadow_master", "taskflow", "eventhub", "ecommerce", "management", "custom"}'
    assert target_modes in content, "target_modes not found"
    content = content.replace(target_modes, replacement_modes, 1)

    # 3. Update resolve_project_mode
    target_detect = """    combined = f"{p_name} {p_desc} {p_cat}".lower()
    if any(k in combined for k in ["carrom", "carromboard", "carrom board", "striker", "carrom master"]):
        return "carrom\""""

    replacement_detect = """    combined = f"{p_name} {p_desc} {p_cat}".lower()
    if any(k in combined for k in ["shadow", "ninja", "stealth", "skill builder", "shadow master", "shadowmaster"]):
        return "shadow_master"
    if any(k in combined for k in ["carrom", "carromboard", "carrom board", "striker", "carrom master"]):
        return "carrom\""""

    assert target_detect in content, "target_detect not found"
    content = content.replace(target_detect, replacement_detect, 1)

    # 4. Anti-collision check
    target_anticollision = """        if not legacy_kanban_collision and not legacy_snake_collision:"""
    replacement_anticollision = """        # Defensive anti-collision check for generic playground files on specialized archetypes
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

        if not legacy_kanban_collision and not legacy_snake_collision and not generic_playground_collision:"""

    assert target_anticollision in content, "target_anticollision not found"
    content = content.replace(target_anticollision, replacement_anticollision, 1)

    # 5. Prototype fallback
    target_proto = """    elif mode == "carrom":
        html = get_carrom_game_html(title=p_name, desc=p_desc)
    elif mode == "eventhub":"""

    replacement_proto = """    elif mode == "carrom":
        html = get_carrom_game_html(title=p_name, desc=p_desc)
    elif mode == "shadow_master":
        html = get_shadow_master_game_html(title=p_name, desc=p_desc)
    elif mode == "eventhub":"""

    assert target_proto in content, "target_proto not found"
    content = content.replace(target_proto, replacement_proto, 1)

    # Validate AST
    ast.parse(content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Updated preview_runtime.py with shadow_master support, AST validated!")

if __name__ == "__main__":
    main()

