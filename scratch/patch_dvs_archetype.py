from pathlib import Path

dvs_path = Path("backend/app/services/development_version_service.py")
if not dvs_path.exists():
    dvs_path = Path("app/services/development_version_service.py")

content = dvs_path.read_text(encoding="utf-8")

# 1. Update register_version_from_workflow to resolve and record authoritative archetype
old_reg = '''            metadata_payload={
                "summary": code_artifact.summary,
                "files": {f.path: f.content for f in code_artifact.generated_files},
                **({"runtime_manifest": artifacts.get("runtime_manifest")} if artifacts.get("runtime_manifest") else {}),
            },'''

new_reg = '''            metadata_payload={
                "summary": code_artifact.summary,
                "files": {f.path: f.content for f in code_artifact.generated_files},
                "archetype": (artifacts.get("archetype") or (project.settings or {}).get("archetype") or "custom"),
                "application_id": (artifacts.get("archetype") or (project.settings or {}).get("archetype") or "custom"),
                **({"runtime_manifest": artifacts.get("runtime_manifest")} if artifacts.get("runtime_manifest") else {}),
            },'''

# 2. Update step 8 in register_version_from_workflow
old_step8 = '''        # 8. Set initial active pointer if no active version exists
        proj_settings = dict(project.settings or {})
        if not proj_settings.get("active_version_id"):
            proj_settings["active_version_id"] = str(version_id)
            project.settings = proj_settings
            flag_modified(project, "settings")'''

new_step8 = '''        # 8. Set initial active pointer if no active version exists and synchronize authoritative archetype
        proj_settings = dict(project.settings or {})
        eff_arch = artifacts.get("archetype") or proj_settings.get("archetype")
        if not proj_settings.get("archetype") and eff_arch:
            proj_settings["archetype"] = eff_arch
        if not proj_settings.get("active_version_id"):
            proj_settings["active_version_id"] = str(version_id)
        project.settings = proj_settings
        flag_modified(project, "settings")'''

# 3. Update activate_version to synchronize project.settings["archetype"]
old_act = '''        # Update Project Active Pointer
        proj_settings["active_version_id"] = str(version_id)
        project.settings = proj_settings
        flag_modified(project, "settings")'''

new_act = '''        # Update Project Active Pointer and Synchronize Authoritative Archetype
        proj_settings["active_version_id"] = str(version_id)
        v_meta = target_version.metadata_payload or {}
        if v_meta.get("archetype"):
            proj_settings["archetype"] = v_meta["archetype"]
        project.settings = proj_settings
        flag_modified(project, "settings")'''

for old_p, new_p in [(old_reg, new_reg), (old_step8, new_step8), (old_act, new_act)]:
    if old_p in content:
        content = content.replace(old_p, new_p, 1)
        print("Replaced LF pattern in development_version_service.py")
    elif old_p.replace("\n", "\r\n") in content:
        content = content.replace(old_p.replace("\n", "\r\n"), new_p.replace("\n", "\r\n"), 1)
        print("Replaced CRLF pattern in development_version_service.py")
    else:
        print("ERROR: Target pattern not found in development_version_service.py")
        exit(1)

dvs_path.write_text(content, encoding="utf-8")
print("Successfully updated development_version_service.py!")
