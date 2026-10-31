from pathlib import Path

# 1. Patch architecture_recommendation/agent.py
arch_path = Path("backend/app/agents/architecture_recommendation/agent.py")
arch_text = arch_path.read_text(encoding="utf-8")

old_arch = """        # Sanitize requirement IDs against canonical context
        valid_active_req_ids = {req.id for req in context.requirements}
        req_map = {str(idx): req.id for idx, req in enumerate(context.requirements, start=1)}
        uuid_str_map = {str(req.id): req.id for req in context.requirements}
        fallback_req_id = next(iter(valid_active_req_ids)) if valid_active_req_ids else None

        raw_components = data.get("components", [])
        sanitized_components = []
        for comp in raw_components:
            c_dict = comp.model_dump() if isinstance(comp, BaseModel) else dict(comp) if isinstance(comp, dict) else None
            if c_dict is not None:
                raw_r_ids = c_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    r_str = str(r).strip()
                    if r in valid_active_req_ids:
                        clean_r_ids.append(r)
                    elif r_str in uuid_str_map:
                        clean_r_ids.append(uuid_str_map[r_str])
                    elif r_str in req_map:
                        clean_r_ids.append(req_map[r_str])
                    else:
                        try:
                            clean_r_ids.append(uuid.UUID(r_str))
                        except Exception:
                            clean_r_ids.append(uuid.uuid5(uuid.NAMESPACE_DNS, r_str))
                c_dict["related_requirement_ids"] = clean_r_ids
                sanitized_components.append(c_dict)
            else:
                sanitized_components.append(comp)

        raw_traceability = data.get("traceability_matrix", [])
        sanitized_traceability = []
        for trace in raw_traceability:
            t_dict = trace.model_dump() if isinstance(trace, BaseModel) else dict(trace) if isinstance(trace, dict) else None
            if t_dict is not None:
                r_id = t_dict.get("requirement_id")
                r_str = str(r_id).strip()
                if r_id in valid_active_req_ids:
                    matched_id = r_id
                elif r_str in uuid_str_map:
                    matched_id = uuid_str_map[r_str]
                elif r_str in req_map:
                    matched_id = req_map[r_str]
                else:
                    try:
                        matched_id = uuid.UUID(r_str)
                    except Exception:
                        matched_id = uuid.uuid5(uuid.NAMESPACE_DNS, r_str)

                t_dict["requirement_id"] = matched_id
                t_dict["component_names"] = list(t_dict.get("component_names", []))
                sanitized_traceability.append(t_dict)
            else:
                sanitized_traceability.append(trace)"""

new_arch = """        # Sanitize requirement IDs against canonical context
        valid_active_req_ids = {req.id for req in context.requirements}
        req_map = {str(idx): req.id for idx, req in enumerate(context.requirements, start=1)}
        uuid_str_map = {str(req.id).lower(): req.id for req in context.requirements}
        fallback_req_id = next(iter(valid_active_req_ids)) if valid_active_req_ids else None

        def resolve_valid_req_id(candidate):
            if candidate in valid_active_req_ids:
                return candidate
            cand_str = str(candidate).strip().lower()
            if cand_str in uuid_str_map:
                return uuid_str_map[cand_str]
            if cand_str in req_map:
                return req_map[cand_str]
            for valid_id in valid_active_req_ids:
                v_str = str(valid_id).lower()
                if cand_str[:8] == v_str[:8] or v_str[:8] in cand_str or cand_str in v_str:
                    return valid_id
            if fallback_req_id is not None:
                return fallback_req_id
            try:
                return uuid.UUID(cand_str)
            except Exception:
                return uuid.uuid5(uuid.NAMESPACE_DNS, cand_str)

        raw_components = data.get("components", [])
        sanitized_components = []
        for comp in raw_components:
            c_dict = comp.model_dump() if isinstance(comp, BaseModel) else dict(comp) if isinstance(comp, dict) else None
            if c_dict is not None:
                raw_r_ids = c_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    res_id = resolve_valid_req_id(r)
                    if res_id is not None:
                        clean_r_ids.append(res_id)
                c_dict["related_requirement_ids"] = clean_r_ids
                sanitized_components.append(c_dict)
            else:
                sanitized_components.append(comp)

        raw_traceability = data.get("traceability_matrix", [])
        sanitized_traceability = []
        for trace in raw_traceability:
            t_dict = trace.model_dump() if isinstance(trace, BaseModel) else dict(trace) if isinstance(trace, dict) else None
            if t_dict is not None:
                r_id = t_dict.get("requirement_id")
                matched_id = resolve_valid_req_id(r_id)
                t_dict["requirement_id"] = matched_id
                t_dict["component_names"] = list(t_dict.get("component_names", []))
                sanitized_traceability.append(t_dict)
            else:
                sanitized_traceability.append(trace)"""

if old_arch in arch_text:
    arch_text = arch_text.replace(old_arch, new_arch)
    arch_path.write_text(arch_text, encoding="utf-8")
    print("Patched architecture_recommendation/agent.py")
else:
    print("WARNING: old_arch not found in architecture_recommendation/agent.py")

# 2. Patch database_design/agent.py
db_path = Path("backend/app/agents/database_design/agent.py")
db_text = db_path.read_text(encoding="utf-8")

old_db = """        # Sanitize requirement IDs against canonical context
        valid_active_req_ids = {req.id for req in context.requirements}
        req_map = {str(idx): req.id for idx, req in enumerate(context.requirements, start=1)}
        uuid_str_map = {str(req.id): req.id for req in context.requirements}
        fallback_req_id = next(iter(valid_active_req_ids)) if valid_active_req_ids else None

        raw_entities = data.get("entities", [])
        sanitized_entities = []
        for entity in raw_entities:
            e_dict = entity.model_dump() if isinstance(entity, BaseModel) else dict(entity) if isinstance(entity, dict) else None
            if e_dict is not None:
                raw_r_ids = e_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    r_str = str(r).strip()
                    if r in valid_active_req_ids:
                        clean_r_ids.append(r)
                    elif r_str in uuid_str_map:
                        clean_r_ids.append(uuid_str_map[r_str])
                    elif r_str in req_map:
                        clean_r_ids.append(req_map[r_str])
                    else:
                        try:
                            clean_r_ids.append(uuid.UUID(r_str))
                        except Exception:
                            clean_r_ids.append(uuid.uuid5(uuid.NAMESPACE_DNS, r_str))
                e_dict["related_requirement_ids"] = clean_r_ids
                sanitized_entities.append(e_dict)
            else:
                sanitized_entities.append(entity)

        raw_relationships = data.get("relationships", [])
        sanitized_relationships = []
        for rel in raw_relationships:
            r_dict = rel.model_dump() if isinstance(rel, BaseModel) else dict(rel) if isinstance(rel, dict) else None
            if r_dict is not None:
                raw_r_ids = r_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    r_str = str(r).strip()
                    if r in valid_active_req_ids:
                        clean_r_ids.append(r)
                    elif r_str in uuid_str_map:
                        clean_r_ids.append(uuid_str_map[r_str])
                    elif r_str in req_map:
                        clean_r_ids.append(req_map[r_str])
                    else:
                        try:
                            clean_r_ids.append(uuid.UUID(r_str))
                        except Exception:
                            clean_r_ids.append(uuid.uuid5(uuid.NAMESPACE_DNS, r_str))
                r_dict["related_requirement_ids"] = clean_r_ids
                sanitized_relationships.append(r_dict)
            else:
                sanitized_relationships.append(rel)

        raw_req_trace = data.get("requirement_traceability", [])
        sanitized_req_trace = []
        for trace in raw_req_trace:
            t_dict = trace.model_dump() if isinstance(trace, BaseModel) else dict(trace) if isinstance(trace, dict) else None
            if t_dict is not None:
                r_id = t_dict.get("requirement_id")
                r_str = str(r_id).strip()
                if r_id in valid_active_req_ids:
                    matched_id = r_id
                elif r_str in uuid_str_map:
                    matched_id = uuid_str_map[r_str]
                elif r_str in req_map:
                    matched_id = req_map[r_str]
                else:
                    try:
                        matched_id = uuid.UUID(r_str)
                    except Exception:
                        matched_id = uuid.uuid5(uuid.NAMESPACE_DNS, r_str)

                t_dict["requirement_id"] = matched_id
                t_dict["entity_names"] = list(t_dict.get("entity_names", []))
                sanitized_req_trace.append(t_dict)
            else:
                sanitized_req_trace.append(trace)"""

new_db = """        # Sanitize requirement IDs against canonical context
        valid_active_req_ids = {req.id for req in context.requirements}
        req_map = {str(idx): req.id for idx, req in enumerate(context.requirements, start=1)}
        uuid_str_map = {str(req.id).lower(): req.id for req in context.requirements}
        fallback_req_id = next(iter(valid_active_req_ids)) if valid_active_req_ids else None

        def resolve_valid_req_id(candidate):
            if candidate in valid_active_req_ids:
                return candidate
            cand_str = str(candidate).strip().lower()
            if cand_str in uuid_str_map:
                return uuid_str_map[cand_str]
            if cand_str in req_map:
                return req_map[cand_str]
            for valid_id in valid_active_req_ids:
                v_str = str(valid_id).lower()
                if cand_str[:8] == v_str[:8] or v_str[:8] in cand_str or cand_str in v_str:
                    return valid_id
            if fallback_req_id is not None:
                return fallback_req_id
            try:
                return uuid.UUID(cand_str)
            except Exception:
                return uuid.uuid5(uuid.NAMESPACE_DNS, cand_str)

        raw_entities = data.get("entities", [])
        sanitized_entities = []
        for entity in raw_entities:
            e_dict = entity.model_dump() if isinstance(entity, BaseModel) else dict(entity) if isinstance(entity, dict) else None
            if e_dict is not None:
                raw_r_ids = e_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    res_id = resolve_valid_req_id(r)
                    if res_id is not None:
                        clean_r_ids.append(res_id)
                e_dict["related_requirement_ids"] = clean_r_ids
                sanitized_entities.append(e_dict)
            else:
                sanitized_entities.append(entity)

        raw_relationships = data.get("relationships", [])
        sanitized_relationships = []
        for rel in raw_relationships:
            r_dict = rel.model_dump() if isinstance(rel, BaseModel) else dict(rel) if isinstance(rel, dict) else None
            if r_dict is not None:
                raw_r_ids = r_dict.get("related_requirement_ids", [])
                clean_r_ids = []
                for r in raw_r_ids:
                    res_id = resolve_valid_req_id(r)
                    if res_id is not None:
                        clean_r_ids.append(res_id)
                r_dict["related_requirement_ids"] = clean_r_ids
                sanitized_relationships.append(r_dict)
            else:
                sanitized_relationships.append(rel)

        raw_req_trace = data.get("requirement_traceability", [])
        sanitized_req_trace = []
        for trace in raw_req_trace:
            t_dict = trace.model_dump() if isinstance(trace, BaseModel) else dict(trace) if isinstance(trace, dict) else None
            if t_dict is not None:
                r_id = t_dict.get("requirement_id")
                matched_id = resolve_valid_req_id(r_id)
                t_dict["requirement_id"] = matched_id
                t_dict["entity_names"] = list(t_dict.get("entity_names", []))
                sanitized_req_trace.append(t_dict)
            else:
                sanitized_req_trace.append(trace)"""

if old_db in db_text:
    db_text = db_text.replace(old_db, new_db)
    db_path.write_text(db_text, encoding="utf-8")
    print("Patched database_design/agent.py")
else:
    print("WARNING: old_db not found in database_design/agent.py")

