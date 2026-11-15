import asyncio
import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.runtime.preview_runtime_manager import preview_runtime_manager

async def start():
    pid = "b9a73557-04a6-4db5-9056-10884a2d5d53"
    success, msg, details = await preview_runtime_manager.ensure_running(
        project_id=pid,
        project_name="Shadow Master Skill Builder",
        project_description="A web-based tool that lets game designers create, preview, and export custom skills for the Shadow Master game."
    )
    print("Preview server start status:", success, msg)
    print("Details:", details)

if __name__ == "__main__":
    asyncio.run(start())
