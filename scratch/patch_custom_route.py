from pathlib import Path

prev_file = Path("app/runtime/preview_server.py")
content = prev_file.read_text(encoding="utf-8")

target = '@app.get("/preview/{project_id}", response_class=HTMLResponse)\ndef preview_project_page(project_id: str):\n    html = get_app_html_for_project(project_id=project_id)\n    return HTMLResponse(content=html)'

replacement = '@app.get("/preview/{project_id}", response_class=HTMLResponse)\ndef preview_project_page(project_id: str):\n    html = get_app_html_for_project(project_id=project_id)\n    return HTMLResponse(content=html)\n\n\n@app.get("/custom", response_class=HTMLResponse)\ndef custom_preview_page(name: Optional[str] = Query("Custom Application"), desc: Optional[str] = Query("")):\n    html = get_custom_interactive_html(name, desc)\n    return HTMLResponse(content=html)'

if target in content:
    content = content.replace(target, replacement, 1)
    prev_file.write_text(content, encoding="utf-8")
    print("Replaced LF in preview_server.py")
elif target.replace("\n", "\r\n") in content:
    content = content.replace(target.replace("\n", "\r\n"), replacement.replace("\n", "\r\n"), 1)
    prev_file.write_text(content, encoding="utf-8")
    print("Replaced CRLF in preview_server.py")
else:
    print("Target not found")

