import sys
import ast

file_path = r"backend/app/main.py"
with open(file_path, "r", encoding="utf-8") as f:
    code = f.read()

if '@app.get("/health")' not in code:
    target = "    return app\n\n\napp = create_application()"
    insertion = """    @app.get("/health")
    def health_root():
        return {"status": "ok", "app": settings.PROJECT_NAME}

    return app


app = create_application()"""
    if target in code:
        code = code.replace(target, insertion)
    else:
        target_crlf = target.replace("\n", "\r\n")
        insertion_crlf = insertion.replace("\n", "\r\n")
        code = code.replace(target_crlf, insertion_crlf)

ast.parse(code)
with open(file_path, "w", encoding="utf-8") as f:
    f.write(code)
print("main.py updated with /health endpoint successfully!")

