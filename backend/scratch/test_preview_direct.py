from app.runtime.preview_server import get_app_html_for_project

pid = "68289eab-12f4-4602-a4b7-143f29c52c58"
html = get_app_html_for_project(project_id=pid)
print("Length:", len(html))
print("Contains 'btn-open-login':", "btn-open-login" in html)
print("Contains 'auth-modal-overlay':", "auth-modal-overlay" in html)
print("Contains 'pwd-meter':", "pwd-meter" in html)
print("Contains 'auth-card':", "auth-card" in html)
print("Contains 'link-forgot-password':", "link-forgot-password" in html)
