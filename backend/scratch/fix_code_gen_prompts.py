with open("app/agents/code_generation/prompts.py", "r", encoding="utf-8") as f:
    code = f.read()

# Check if arch is already replaced or not
old_arch = """    if architecture_recommendation:
        arch_lines = [f"Summary: {architecture_recommendation.summary}"]
        if architecture_recommendation.architecture_styles:
            arch_lines.append(f"Styles: {', '.join(s.style.value for s in architecture_recommendation.architecture_styles)}")
        if architecture_recommendation.components:
            arch_lines.append("Components:")
            for c in architecture_recommendation.components:
                arch_lines.append(f"  - {c.name}: {c.responsibility}")
        arch_block = "\\n".join(arch_lines)"""

new_arch = """    if architecture_recommendation:
        if isinstance(architecture_recommendation, dict):
            summary = architecture_recommendation.get("summary", "None provided.")
            styles = architecture_recommendation.get("architecture_styles", [])
            comps = architecture_recommendation.get("components", [])
            arch_lines = [f"Summary: {summary}"]
            if styles:
                style_names = [s.get("style", "") if isinstance(s, dict) else getattr(s, "style", "") for s in styles]
                arch_lines.append(f"Styles: {', '.join(str(s) for s in style_names if s)}")
            if comps:
                arch_lines.append("Components:")
                for c in comps:
                    c_name = c.get("name", "") if isinstance(c, dict) else getattr(c, "name", "")
                    c_resp = c.get("responsibility", "") if isinstance(c, dict) else getattr(c, "responsibility", "")
                    arch_lines.append(f"  - {c_name}: {c_resp}")
            arch_block = "\\n".join(arch_lines)
        else:
            arch_lines = [f"Summary: {architecture_recommendation.summary}"]
            if architecture_recommendation.architecture_styles:
                arch_lines.append(f"Styles: {', '.join(s.style.value for s in architecture_recommendation.architecture_styles)}")
            if architecture_recommendation.components:
                arch_lines.append("Components:")
                for c in architecture_recommendation.components:
                    arch_lines.append(f"  - {c.name}: {c.responsibility}")
            arch_block = "\\n".join(arch_lines)"""

if old_arch in code:
    code = code.replace(old_arch, new_arch, 1)

old_db = """    if database_design:
        db_lines = [f"Paradigm: {database_design.database_paradigm.value}"]
        if database_design.entities:
            db_lines.append("Logical Entities:")
            for e in database_design.entities:
                attrs = ", ".join(f"{a.name} ({a.data_type.value})" for a in e.attributes[:6])
                db_lines.append(f"  - {e.name}: [{attrs}]")
            db_block = "\\n".join(db_lines)"""

new_db = """    if database_design:
        if isinstance(database_design, dict):
            paradigm = database_design.get("database_paradigm", "relational")
            entities = database_design.get("entities", [])
            db_lines = [f"Paradigm: {paradigm}"]
            if entities:
                db_lines.append("Logical Entities:")
                for e in entities:
                    e_name = e.get("name", "") if isinstance(e, dict) else getattr(e, "name", "")
                    attrs = e.get("attributes", []) if isinstance(e, dict) else getattr(e, "attributes", [])
                    attr_strs = []
                    for a in attrs[:6]:
                        a_name = a.get("name", "") if isinstance(a, dict) else getattr(a, "name", "")
                        a_type = a.get("data_type", "") if isinstance(a, dict) else getattr(a, "data_type", "")
                        attr_strs.append(f"{a_name} ({a_type})")
                    db_lines.append(f"  - {e_name}: [{', '.join(attr_strs)}]")
            db_block = "\\n".join(db_lines)
        else:
            db_lines = [f"Paradigm: {database_design.database_paradigm.value}"]
            if database_design.entities:
                db_lines.append("Logical Entities:")
                for e in database_design.entities:
                    attrs = ", ".join(f"{a.name} ({a.data_type.value})" for a in e.attributes[:6])
                    db_lines.append(f"  - {e.name}: [{attrs}]")
            db_block = "\\n".join(db_lines)"""

if old_db in code:
    code = code.replace(old_db, new_db, 1)

old_db2 = '    if database_design and database_design.entities:\n        db_summary = f"Entities: {\', \'.join(e.name for e in database_design.entities)}"'
new_db2 = """    if database_design:
        if isinstance(database_design, dict):
            entities = database_design.get("entities", [])
            if entities:
                names = [e.get("name", "") if isinstance(e, dict) else getattr(e, "name", "") for e in entities]
                db_summary = f"Entities: {', '.join(n for n in names if n)}"
        elif database_design.entities:
            db_summary = f"Entities: {', '.join(e.name for e in database_design.entities)}\""""

if old_db2 in code:
    code = code.replace(old_db2, new_db2, 1)

with open("app/agents/code_generation/prompts.py", "w", encoding="utf-8") as f:
    f.write(code)

print("Prompts.py updated successfully!")
