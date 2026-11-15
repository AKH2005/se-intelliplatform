from pathlib import Path

# Load test html generator
engine_path = Path("scratch/test_sky_strike_engine.py")
if not engine_path.exists():
    engine_path = Path("../scratch/test_sky_strike_engine.py")

with open(engine_path, "r", encoding="utf-8") as f:
    engine_code = f.read()

# Extract just the function definition of get_sky_strike_game_html
start_idx = engine_code.find("def get_sky_strike_game_html")
end_idx = engine_code.find('if __name__ == "__main__":')
game_func_code = engine_code[start_idx:end_idx].strip()

prev_path = Path("backend/app/runtime/preview_server.py")
if not prev_path.exists():
    prev_path = Path("app/runtime/preview_server.py")

content = prev_path.read_text(encoding="utf-8")

# Check if already present
if "def get_sky_strike_game_html" in content:
    print("get_sky_strike_game_html already present in preview_server.py")
else:
    # Insert right before get_custom_interactive_html
    target = "def get_custom_interactive_html("
    replacement = game_func_code + "\n\n\n" + target
    if target in content:
        content = content.replace(target, replacement, 1)
        print("Inserted get_sky_strike_game_html function!")
    else:
        print("ERROR: Target get_custom_interactive_html not found")
        exit(1)

# Now add the routing branch in get_custom_interactive_html
route_target = '    # 1. MEDICAL / HEALTHCARE'
route_addition = '''    # 0. AERIAL COMBAT & FLIGHT ACTION GAMES (e.g. Sky Strike)
    if _has_kw("flight", "aerial", "sky", "strike", "aircraft", "dogfight", "jet", "plane", "arcade", "combat", "shooter", "air combat", "fighter jet", "interceptor", "space combat"):
        app_title = title if title and "SE IntelliPlatform" not in title else "Sky Strike"
        app_desc = desc if desc else "Fast-paced aerial combat game with real-time dogfights, dynamic weather, upgradeable aircraft, and avionics HUD."
        return get_sky_strike_game_html(title=app_title, desc=app_desc)

    # 1. MEDICAL / HEALTHCARE'''

if "# 0. AERIAL COMBAT & FLIGHT ACTION GAMES" not in content:
    if route_target in content:
        content = content.replace(route_target, route_addition, 1)
        print("Inserted aerial combat routing branch!")
    else:
        print("ERROR: route_target not found")
        exit(1)
else:
    print("Aerial combat routing branch already present")

prev_path.write_text(content, encoding="utf-8")
print("Successfully updated preview_server.py!")
