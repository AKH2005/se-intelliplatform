import sys
sys.path.insert(0, "backend")

from app.agents.code_generation.archetypes import detect_project_archetype

name = "Sky Strike"
desc = "Sky Strike is a fast-paced aerial combat game that pits players against each other in real-time dogfights. It offers dynamic weather, upgradeable aircraft, and cross-platform play to deliver an immersive and competitive experience."

arch = detect_project_archetype(name=name, desc=desc)
print(f"detect_project_archetype('{name}') => '{arch}'")
