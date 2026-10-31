with open('backend/app/runtime/preview_server.py', 'r', encoding='utf-8') as f:
    content = f.read()

# Normalize CRLF to LF
content = content.replace('\r\n', '\n')

old_part = """def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    if runtime_features.get("dark_mode", False):
        return True
    target_pid = project_id or active_project_context.get("project_id")"""

new_part = """def is_dark_mode_active(project_id: Optional[str] = None) -> bool:
    target_pid = project_id or active_project_context.get("project_id")"""

if old_part in content:
    content = content.replace(old_part, new_part)
    with open('backend/app/runtime/preview_server.py', 'w', encoding='utf-8', newline='\n') as f:
        f.write(content)
    print("Successfully updated preview_server.py")
else:
    print("old_part not found")

