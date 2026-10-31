from pathlib import Path

# 1. Patch architecture_recommendation/agent.py
agent_file = Path("backend/app/agents/architecture_recommendation/agent.py")
content = agent_file.read_text(encoding="utf-8").replace("\r\n", "\n")

target_arch = """        # 3. Construct authoritative ArchitectureRecommendationOutput
        final_output = ArchitectureRecommendationOutput(
            summary=data.get("summary", "Architecture recommendation generated."),
            architecture_styles=data.get("architecture_styles", []),
            components=sanitized_components,
            data_flows=data.get("data_flows", []),
            technologies=data.get("technologies", []),
            trade_offs=data.get("trade_offs", []),
            assumptions=data.get("assumptions", []),
            constraints=data.get("constraints", []),
            unknowns=data.get("unknowns", []),
            traceability_matrix=sanitized_traceability,
        )"""

replacement_arch = """        # Collect declared component names
        declared_names = set()
        for comp in sanitized_components:
            name = comp.get("name") if isinstance(comp, dict) else getattr(comp, "name", None)
            if name:
                declared_names.add(str(name))

        default_source = next(iter(declared_names)) if declared_names else "Frontend Application"
        default_target = next((d for d in declared_names if d != default_source), default_source)

        def resolve_comp_name(candidate, fallback):
            cand_str = str(candidate or "").strip()
            if cand_str in declared_names:
                return cand_str
            for d in declared_names:
                if d.lower() == cand_str.lower():
                    return d
            for d in declared_names:
                if cand_str.lower() in d.lower() or d.lower() in cand_str.lower():
                    return d
            return fallback

        raw_flows = data.get("data_flows", [])
        sanitized_flows = []
        for flow in raw_flows:
            f_dict = flow.model_dump() if hasattr(flow, "model_dump") else dict(flow) if isinstance(flow, dict) else None
            if f_dict is not None:
                src = resolve_comp_name(f_dict.get("source_component", ""), default_source)
                tgt = resolve_comp_name(f_dict.get("target_component", ""), default_target)
                if src == tgt and len(declared_names) > 1:
                    alt = next((d for d in declared_names if d != src), None)
                    if alt:
                        tgt = alt
                f_dict["source_component"] = src
                f_dict["target_component"] = tgt
                sanitized_flows.append(f_dict)
            else:
                sanitized_flows.append(flow)

        # 3. Construct authoritative ArchitectureRecommendationOutput
        final_output = ArchitectureRecommendationOutput(
            summary=data.get("summary", "Architecture recommendation generated."),
            architecture_styles=data.get("architecture_styles", []),
            components=sanitized_components,
            data_flows=sanitized_flows,
            technologies=data.get("technologies", []),
            trade_offs=data.get("trade_offs", []),
            assumptions=data.get("assumptions", []),
            constraints=data.get("constraints", []),
            unknowns=data.get("unknowns", []),
            traceability_matrix=sanitized_traceability,
        )"""

if target_arch in content:
    content = content.replace(target_arch, replacement_arch)
    agent_file.write_text(content, encoding="utf-8")
    print("Patched architecture_recommendation/agent.py")
else:
    print("Target not found in architecture_recommendation/agent.py")

# 2. Patch code_generation/planning_agent.py
plan_file = Path("backend/app/agents/code_generation/planning_agent.py")
plan_content = plan_file.read_text(encoding="utf-8").replace("\r\n", "\n")

target_plan = """        elif fullstack:
            has_frontend = any(
                ("frontend/" in (f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))))
                or ("package.json" in (f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))))
                for f in raw_files
            )
            if not has_frontend:
                logger.info("Candidate plan lacked required frontend files for fullstack project; using complete fullstack scaffold.")
                raw_files = self._build_mock_files(context, arch_rec)"""

replacement_plan = """        elif fullstack:
            has_frontend = any(
                ("frontend/" in (f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))))
                or ("package.json" in (f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))))
                for f in raw_files
            )
            has_backend = any(
                any((f.path if isinstance(f, (PlannedFile, PlannedFileCandidate)) else (f.get("path") or f.get("file_path", ""))).lower().endswith(ext) for ext in ["main.py", "requirements.txt", "api.py"])
                for f in raw_files
            )
            if not has_frontend or not has_backend:
                logger.info("Candidate plan lacked required frontend or backend files for fullstack project; using complete fullstack scaffold.")
                raw_files = self._build_mock_files(context, arch_rec)"""

if target_plan in plan_content:
    plan_content = plan_content.replace(target_plan, replacement_plan)
    plan_file.write_text(plan_content, encoding="utf-8")
    print("Patched code_generation/planning_agent.py")
else:
    print("Target not found in code_generation/planning_agent.py")

