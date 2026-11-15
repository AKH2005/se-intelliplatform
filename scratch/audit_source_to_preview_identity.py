import asyncio
import hashlib
import json
import os
import sys
import uuid
from sqlalchemy import select

sys.path.insert(0, os.path.abspath("backend"))

from app.core.database import AsyncSessionLocal
from app.models.project import Project
from app.models.development_version import DevelopmentVersion
from app.services.project_download_service import ProjectDownloadService

def compute_hash(text: str) -> str:
    # Normalize line endings
    norm = text.replace("\r\n", "\n").strip()
    return hashlib.sha256(norm.encode("utf-8")).hexdigest()

async def audit_projects():
    print("=== SOURCE-TO-PREVIEW IDENTITY AUDIT ===")
    async with AsyncSessionLocal() as session:
        stmt = select(Project).order_by(Project.created_at.desc())
        res = await session.execute(stmt)
        projects = res.scalars().all()

        pds = ProjectDownloadService(session)

        print(f"Total Projects in Database: {len(projects)}")
        report_rows = []

        for p in projects:
            p_name = p.name or "Untitled"
            p_id = str(p.id)
            settings = p.settings or {}
            act_ver_id = settings.get("active_version_id")

            # Load project files from active version
            files_map = await pds.get_project_files(p.id)
            entry_path = "frontend/index.html" if "frontend/index.html" in files_map else "index.html" if "index.html" in files_map else None

            gen_hash = "N/A"
            gen_len = 0
            has_files = False
            fallback_used = False

            if entry_path and entry_path in files_map:
                entry_content = files_map[entry_path]
                gen_hash = compute_hash(entry_content)
                gen_len = len(entry_content)
                has_files = True
            else:
                fallback_used = True

            # Check version details
            ver_num = None
            manifest_ref = None
            if act_ver_id:
                try:
                    v_uuid = uuid.UUID(act_ver_id)
                    v_stmt = select(DevelopmentVersion).where(DevelopmentVersion.id == v_uuid)
                    v_res = await session.execute(v_stmt)
                    dev_ver = v_res.scalar_one_or_none()
                    if dev_ver:
                        ver_num = dev_ver.version_number
                        manifest_ref = dev_ver.manifest_hash or f"files_manifest({dev_ver.file_count} files)"
                except Exception:
                    pass

            row = {
                "project_name": p_name,
                "project_id": p_id,
                "active_version_id": act_ver_id or "None",
                "version_number": f"v{ver_num}" if ver_num else "Unversioned",
                "entry_file_path": entry_path or "archetype_starter_prototype",
                "file_count": len(files_map),
                "generated_entry_hash": gen_hash,
                "runtime_manifest_ref": manifest_ref or "archetype_scaffold",
                "fallback_content_used": "YES (Archetype Prototype)" if fallback_used else "NO (Authentic Version Files)",
            }
            report_rows.append(row)
            print(f"\nProject: {p_name} ({p_id})")
            print(f"  Active Version: {row['active_version_id']} ({row['version_number']})")
            print(f"  Files in Manifest: {row['file_count']}")
            print(f"  Entry File: {row['entry_file_path']}")
            print(f"  Generated Hash: {row['generated_entry_hash']}")
            print(f"  Fallback Used: {row['fallback_content_used']}")

    with open("scratch/source_identity_audit.json", "w", encoding="utf-8") as f:
        json.dump(report_rows, f, indent=2)
    print("\nSaved scratch/source_identity_audit.json successfully!")

if __name__ == "__main__":
    asyncio.run(audit_projects())