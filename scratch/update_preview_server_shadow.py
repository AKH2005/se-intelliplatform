import os
import ast

def main():
    path = r"backend\app\runtime\preview_server.py"
    with open(path, "r", encoding="utf-8") as f:
        content = f.read()

    # 1. Update detect_mode
    target_detect = """def detect_mode(name: str = "", desc: str = "") -> str:
    combined = f"{name} {desc}".lower()
    if any(k in combined for k in ["carrom", "carromboard", "carrom board", "striker", "carrom master"]):
        return "carrom\""""

    replacement_detect = """def detect_mode(name: str = "", desc: str = "") -> str:
    combined = f"{name} {desc}".lower()
    if any(k in combined for k in ["shadow", "ninja", "stealth", "skill builder", "shadow master", "shadowmaster"]):
        return "shadow_master"
    if any(k in combined for k in ["carrom", "carromboard", "carrom board", "striker", "carrom master"]):
        return "carrom\""""

    assert target_detect in content, "target_detect not found"
    content = content.replace(target_detect, replacement_detect, 1)

    # 2. Update p_arch set
    target_arch_set = 'mode = p_arch if p_arch in {"analytics", "snake_game", "carrom", "taskflow", "eventhub", "ecommerce", "management", "custom"} else detect_mode(p_name, p_desc)'
    replacement_arch_set = 'mode = p_arch if p_arch in {"analytics", "snake_game", "carrom", "shadow_master", "taskflow", "eventhub", "ecommerce", "management", "custom"} else detect_mode(p_name, p_desc)'
    assert target_arch_set in content, "target_arch_set not found"
    content = content.replace(target_arch_set, replacement_arch_set, 1)

    # 3. Update mode dispatch
    target_mode_dispatch = """    elif mode == "carrom":
        return get_carrom_game_html(p_name or "Carrom Master", p_desc)
    elif mode == "ecommerce":"""

    replacement_mode_dispatch = """    elif mode == "carrom":
        return get_carrom_game_html(p_name or "Carrom Master", p_desc)
    elif mode == "shadow_master":
        return get_shadow_master_game_html(p_name or "Shadow Master Skill Builder", p_desc)
    elif mode == "ecommerce":"""

    assert target_mode_dispatch in content, "target_mode_dispatch not found"
    content = content.replace(target_mode_dispatch, replacement_mode_dispatch, 1)

    # 4. Update workspace anti-collision check
    target_ws = """                for cand in candidates:
                    if cand.is_file():
                        return cand.read_text(encoding="utf-8", errors="replace")"""

    replacement_ws = """                for cand in candidates:
                    if cand.is_file():
                        c_text = cand.read_text(encoding="utf-8", errors="replace")
                        if "Interactive Application Playground" not in c_text or mode == "custom":
                            return c_text"""

    assert target_ws in content, "target_ws not found"
    content = content.replace(target_ws, replacement_ws, 1)

    # 5. Extract get_shadow_master_game_html from build_shadow_master_html.py
    b_path = r"C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\scratch\build_shadow_master_html.py"
    if not os.path.exists(b_path):
        b_path = r"scratch\build_shadow_master_html.py"
    with open(b_path, "r", encoding="utf-8") as f:
        b_content = f.read()

    # The function starts with def generate_shadow_master_html and ends right before if __name__ == "__main__":
    start_marker = 'def generate_shadow_master_html(title="Shadow Master Skill Builder", desc=""):'
    end_marker = 'if __name__ == "__main__":'
    idx_start = b_content.find(start_marker)
    idx_end = b_content.find(end_marker)
    assert idx_start != -1 and idx_end != -1, "Could not locate generate_shadow_master_html in build_shadow_master_html.py"

    func_code = b_content[idx_start:idx_end].strip()
    func_code = func_code.replace(
        'def generate_shadow_master_html(title="Shadow Master Skill Builder", desc=""):',
        'def get_shadow_master_game_html(title: str = "Shadow Master Skill Builder", desc: str = "") -> str:'
    )

    target_insert_pos = 'def get_ecommerce_html(title: str = "ShopSphere", desc: str = "") -> str:'
    assert target_insert_pos in content, "target_insert_pos not found"
    content = content.replace(target_insert_pos, func_code + "\n\n\n" + target_insert_pos, 1)

    # 6. Add route @app.get("/shadow_master")
    endpoint_target = """@app.get("/carrom", response_class=HTMLResponse)
def carrom_page():
    return HTMLResponse(content=get_carrom_game_html())"""

    endpoint_replacement = """@app.get("/carrom", response_class=HTMLResponse)
def carrom_page():
    return HTMLResponse(content=get_carrom_game_html())


@app.get("/shadow_master", response_class=HTMLResponse)
def shadow_master_page():
    return HTMLResponse(content=get_shadow_master_game_html())"""

    assert endpoint_target in content, "endpoint_target not found"
    content = content.replace(endpoint_target, endpoint_replacement, 1)

    # Validate with AST before saving
    ast.parse(content)

    with open(path, "w", encoding="utf-8") as f:
        f.write(content)
    print("SUCCESS: Updated preview_server.py with shadow_master support and AST validated!")

if __name__ == "__main__":
    main()
