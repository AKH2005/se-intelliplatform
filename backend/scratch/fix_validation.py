with open('app/agents/code_generation/validation.py', 'r', encoding='utf-8') as f:
    code = f.read()

old_trace = '''    # 5. Architecture Component Traceability
    if architecture_recommendation is not None and hasattr(architecture_recommendation, "components"):
        declared_components = {c.name for c in architecture_recommendation.components}
        for f in plan.files:
            if f.architecture_component and f.architecture_component not in declared_components:
                errors.append(
                    f"File '{f.path}' references undeclared architecture component '{f.architecture_component}'. "
                    f"Declared: {sorted(declared_components)}"
                )'''

new_trace = '''    # 5. Architecture Component Traceability
    if architecture_recommendation is not None:
        if isinstance(architecture_recommendation, dict):
            components_list = architecture_recommendation.get("components", [])
            declared_components = {
                c.get("name") if isinstance(c, dict) else getattr(c, "name", "")
                for c in components_list
            }
        elif hasattr(architecture_recommendation, "components") and architecture_recommendation.components:
            declared_components = {c.name for c in architecture_recommendation.components}
        else:
            declared_components = set()

        if declared_components:
            for f in plan.files:
                if f.architecture_component and f.architecture_component not in declared_components:
                    errors.append(
                        f"File '{f.path}' references undeclared architecture component '{f.architecture_component}'. "
                        f"Declared: {sorted(declared_components)}"
                    )'''

assert old_trace in code, 'old_trace not found'
code = code.replace(old_trace, new_trace, 1)

with open('app/agents/code_generation/validation.py', 'w', encoding='utf-8') as f:
    f.write(code)

print('Updated validation.py')
