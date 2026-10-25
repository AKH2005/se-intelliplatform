# 1. Update prompts.py
with open("app/agents/code_generation/prompts.py", "r", encoding="utf-8") as f:
    code = f.read()

old_req = """    req_lines = [
        f"[{idx}] UUID: {r.id} | Title: {r.title} | Priority: {r.priority.value}\\n    Description: {r.description.strip()}"
        for idx, r in enumerate(requirements, start=1)
    ]"""

new_req = """    req_lines = [
        f"Requirement ID: {r.id} | Title: {r.title} | Priority: {r.priority.value}\\n    Description: {r.description.strip()}"
        for r in requirements
    ]"""

if old_req in code:
    code = code.replace(old_req, new_req, 1)
    with open("app/agents/code_generation/prompts.py", "w", encoding="utf-8") as f:
        f.write(code)
    print("Updated prompts.py requirements format.")
else:
    print("Could not find old_req in prompts.py")

# 2. Update planning_agent.py
with open("app/agents/code_generation/planning_agent.py", "r", encoding="utf-8") as f:
    code_plan = f.read()

old_plan_req = "                reqs = f.requirement_ids if isinstance(f, PlannedFileCandidate) else f.get(\"requirement_ids\", [])"
new_plan_req = """                raw_reqs = f.requirement_ids if isinstance(f, PlannedFileCandidate) else f.get("requirement_ids", [])
                canonical_uuids = {str(r.id) for r in context.requirements}
                req_map = {str(idx): str(r.id) for idx, r in enumerate(context.requirements, start=1)}
                reqs = []
                for r_id in raw_reqs:
                    r_str = str(r_id).strip()
                    if r_str in canonical_uuids:
                        reqs.append(r_str)
                    elif r_str in req_map:
                        reqs.append(req_map[r_str])"""

if old_plan_req in code_plan:
    code_plan = code_plan.replace(old_plan_req, new_plan_req, 1)
    with open("app/agents/code_generation/planning_agent.py", "w", encoding="utf-8") as f:
        f.write(code_plan)
    print("Updated planning_agent.py requirement mapping.")
else:
    print("Could not find old_plan_req in planning_agent.py")

# 3. Update generation_agent.py
with open("app/agents/code_generation/generation_agent.py", "r", encoding="utf-8") as f:
    code_gen = f.read()

old_gen_req = "                reqs = cf.requirement_ids if isinstance(cf, GeneratedFileCandidate) else cf.get(\"requirement_ids\", [])"
new_gen_req = """                raw_reqs = cf.requirement_ids if isinstance(cf, GeneratedFileCandidate) else cf.get("requirement_ids", [])
                canonical_uuids = {str(r.id) for r in context.requirements}
                req_map = {str(idx): str(r.id) for idx, r in enumerate(context.requirements, start=1)}
                reqs = []
                for r_id in raw_reqs:
                    r_str = str(r_id).strip()
                    if r_str in canonical_uuids:
                        reqs.append(r_str)
                    elif r_str in req_map:
                        reqs.append(req_map[r_str])"""

if old_gen_req in code_gen:
    code_gen = code_gen.replace(old_gen_req, new_gen_req, 1)
    with open("app/agents/code_generation/generation_agent.py", "w", encoding="utf-8") as f:
        f.write(code_gen)
    print("Updated generation_agent.py requirement mapping.")
else:
    print("Could not find old_gen_req in generation_agent.py")
