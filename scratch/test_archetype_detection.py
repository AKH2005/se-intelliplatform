import sys
from pathlib import Path
sys.path.insert(0, str(Path("backend").resolve()))

from app.agents.code_generation.archetypes import detect_project_archetype

cases = [
    ("EventHub Conference Portal", "Modern event booking and ticket management"),
    ("Apex Inventory & Warehouse Manager", "Enterprise SKU stock tracking, supplier management, and adjustments"),
    ("SkillForge Online Academy", "Interactive technical courses, lessons, and student progress"),
    ("CyberMart Developer Equipment Store", "Developer workstation storefront with shopping cart and checkout"),
    ("Sky Strike Dogfight Simulator", "60 FPS aerial combat simulator with flight controls and scoring"),
]

for name, desc in cases:
    archetype = detect_project_archetype(name=name, desc=desc)
    print(f"[{archetype}] {name}")
