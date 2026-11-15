from pathlib import Path

file_path = Path("backend/app/agents/code_generation/archetypes.py")
if not file_path.exists():
    file_path = Path("app/agents/code_generation/archetypes.py")

content = file_path.read_text(encoding="utf-8")

# 1. Precise shadow_master keywords
old_shadow = '    if _has_word(combined, "shadow master", "shadowmaster", "shadow", "skill builder",\n                 "ninja", "stealth", "katana", "combat arena", "martial arts", "action game", "fighter"):\n        return "shadow_master"'

new_shadow = '    if _has_word(combined, "shadow master", "shadowmaster", "shadow combat", "shadow skill",\n                 "ninja combat", "stealth ninja", "katana slash", "shadow warrior", "shadow duel", "skill builder"):\n        return "shadow_master"'

# 2. General game category fallback MUST NOT force shadow_master
old_game_fallback = '    if cat == "GAME":\n        if _has_word(combined, "board game", "turn-based board"):\n            return "chess"\n        return "shadow_master"'

new_game_fallback = '    if cat == "GAME":\n        if _has_word(combined, "board game", "turn-based board"):\n            return "chess"\n        return "custom"'

# Handle LF and CRLF
found1 = False
found2 = False

if old_shadow in content:
    content = content.replace(old_shadow, new_shadow, 1)
    found1 = True
elif old_shadow.replace("\n", "\r\n") in content:
    content = content.replace(old_shadow.replace("\n", "\r\n"), new_shadow.replace("\n", "\r\n"), 1)
    found1 = True

if old_game_fallback in content:
    content = content.replace(old_game_fallback, new_game_fallback, 1)
    found2 = True
elif old_game_fallback.replace("\n", "\r\n") in content:
    content = content.replace(old_game_fallback.replace("\n", "\r\n"), new_game_fallback.replace("\n", "\r\n"), 1)
    found2 = True

print(f"Shadow keywords patched: {found1}")
print(f"Game fallback patched: {found2}")

if found1 and found2:
    file_path.write_text(content, encoding="utf-8")
    print("Successfully updated archetypes.py!")
else:
    print("ERROR: Could not find target patterns in archetypes.py")
    exit(1)
