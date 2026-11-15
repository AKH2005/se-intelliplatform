from pathlib import Path

# 1. Patch planning_agent.py
plan_path = Path("backend/app/agents/code_generation/planning_agent.py")
if not plan_path.exists():
    plan_path = Path("app/agents/code_generation/planning_agent.py")

p_content = plan_path.read_text(encoding="utf-8")

old_plan = '''        if fullstack:
            archetype = detect_project_archetype(
                name=context.project.name,
                desc=context.project.description or "",
                slug=context.project.slug or "",
            )'''

new_plan = '''        if fullstack:
            archetype = (
                context.project.settings.get("archetype")
                if hasattr(context.project, "settings") and isinstance(context.project.settings, dict)
                else None
            )
            if not archetype:
                archetype = detect_project_archetype(
                    name=context.project.name,
                    desc=context.project.description or "",
                    slug=context.project.slug or "",
                )'''

if old_plan in p_content:
    p_content = p_content.replace(old_plan, new_plan, 1)
    print("Replaced LF in planning_agent.py")
elif old_plan.replace("\n", "\r\n") in p_content:
    p_content = p_content.replace(old_plan.replace("\n", "\r\n"), new_plan.replace("\n", "\r\n"), 1)
    print("Replaced CRLF in planning_agent.py")
else:
    print("ERROR: old_plan not found in planning_agent.py")
    exit(1)

plan_path.write_text(p_content, encoding="utf-8")

# 2. Patch generation_agent.py
gen_path = Path("backend/app/agents/code_generation/generation_agent.py")
if not gen_path.exists():
    gen_path = Path("app/agents/code_generation/generation_agent.py")

g_content = gen_path.read_text(encoding="utf-8")

old_gen_1 = '''        archetype = detect_project_archetype(
            name=context.project.name,
            desc=context.project.description or "",
            slug=context.project.slug or "",
        )'''

new_gen_1 = '''        archetype = (
            context.project.settings.get("archetype")
            if hasattr(context.project, "settings") and isinstance(context.project.settings, dict)
            else None
        )
        if not archetype:
            archetype = detect_project_archetype(
                name=context.project.name,
                desc=context.project.description or "",
                slug=context.project.slug or "",
            )'''

# Replace all occurrences in generation_agent.py
if old_gen_1 in g_content:
    g_content = g_content.replace(old_gen_1, new_gen_1)
    print("Replaced LF occurrences in generation_agent.py")
elif old_gen_1.replace("\n", "\r\n") in g_content:
    g_content = g_content.replace(old_gen_1.replace("\n", "\r\n"), new_gen_1.replace("\n", "\r\n"))
    print("Replaced CRLF occurrences in generation_agent.py")
else:
    print("ERROR: old_gen_1 not found in generation_agent.py")
    exit(1)

gen_path.write_text(g_content, encoding="utf-8")
print("Successfully patched planning_agent.py and generation_agent.py!")
