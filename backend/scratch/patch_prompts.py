with open('app/agents/code_generation/prompts.py', 'r', encoding='utf-8') as f:
    lines = f.readlines()

new_lines = []
i = 0
while i < len(lines):
    line = lines[i]
    if 'if database_design:' in line and 'db_lines = [' in lines[i+1]:
        indent = '    '
        new_lines.append(f'{indent}if database_design:\n')
        new_lines.append(f'{indent}    if isinstance(database_design, dict):\n')
        new_lines.append(f'{indent}        paradigm = database_design.get("database_paradigm", "relational")\n')
        new_lines.append(f'{indent}        entities = database_design.get("entities", [])\n')
        new_lines.append(f'{indent}        db_lines = [f"Paradigm: {{paradigm}}"]\n')
        new_lines.append(f'{indent}        if entities:\n')
        new_lines.append(f'{indent}            db_lines.append("Logical Entities:")\n')
        new_lines.append(f'{indent}            for e in entities:\n')
        new_lines.append(f'{indent}                e_name = e.get("name", "") if isinstance(e, dict) else getattr(e, "name", "")\n')
        new_lines.append(f'{indent}                attrs = e.get("attributes", []) if isinstance(e, dict) else getattr(e, "attributes", [])\n')
        new_lines.append(f'{indent}                attr_strs = []\n')
        new_lines.append(f'{indent}                for a in attrs[:6]:\n')
        new_lines.append(f'{indent}                    a_name = a.get("name", "") if isinstance(a, dict) else getattr(a, "name", "")\n')
        new_lines.append(f'{indent}                    a_type = a.get("data_type", "") if isinstance(a, dict) else getattr(a, "data_type", "")\n')
        new_lines.append(f'{indent}                    attr_strs.append(f"{{a_name}} ({{a_type}})")\n')
        new_lines.append(f'{indent}                joined_attrs = ", ".join(attr_strs)\n')
        new_lines.append(f'{indent}                db_lines.append(f"  - {{e_name}}: [{{joined_attrs}}]")\n')
        new_lines.append(f'{indent}        db_block = "\\n".join(db_lines)\n')
        new_lines.append(f'{indent}    else:\n')
        j = i + 1
        while j < len(lines) and 'db_block =' not in lines[j]:
            new_lines.append('    ' + lines[j])
            j += 1
        if j < len(lines):
            new_lines.append('    ' + lines[j])
            j += 1
        i = j
    else:
        new_lines.append(line)
        i += 1

with open('app/agents/code_generation/prompts.py', 'w', encoding='utf-8') as f:
    f.writelines(new_lines)

print('Successfully patched database_design in prompts.py')
