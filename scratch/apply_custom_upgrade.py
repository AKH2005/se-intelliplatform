import ast
import re
from pathlib import Path
import sys
sys.path.insert(0, ".")

from scratch.upgrade_custom_generator import generate_custom_html_engine

new_engine_code = generate_custom_html_engine()

# 1. Update preview_server.py
ps_path = Path("backend/app/runtime/preview_server.py")
ps_content = ps_path.read_text(encoding="utf-8")

# Find def get_custom_interactive_html(
func_start = ps_content.find("def get_custom_interactive_html(")
if func_start == -1:
    raise ValueError("Could not find get_custom_interactive_html in preview_server.py")

# Find the end of that function: it ends before the next def get_app_html_for_project
func_end = ps_content.find("def get_chess_game_html(", func_start)
if func_end == -1:
    func_end = ps_content.find("def get_app_html_for_project(", func_start)

if func_end == -1:
    raise ValueError("Could not find end of get_custom_interactive_html")

ps_content = ps_content[:func_start] + new_engine_code + "\n\n" + ps_content[func_end:]

ast.parse(ps_content, filename="preview_server.py")
ps_path.write_text(ps_content, encoding="utf-8")
print("SUCCESS: Updated preview_server.py with domain-adaptive custom engine!")

# 2. Update build_all_archetype_engines.py as well
b_path = Path("scratch/build_all_archetype_engines.py")
b_content = b_path.read_text(encoding="utf-8")
b_start = b_content.find("def get_custom_interactive_html(")
if b_start != -1:
    b_content = b_content[:b_start] + new_engine_code
    ast.parse(b_content, filename="build_all_archetype_engines.py")
    b_path.write_text(b_content, encoding="utf-8")
    print("SUCCESS: Updated scratch/build_all_archetype_engines.py!")

