from app.agents.code_generation.archetypes import detect_project_archetype

mode = detect_project_archetype("Shadow Duel", "A fast-paced 2D fighting game where players control shadow avatars in dynamic arenas")
print("Detected mode for Shadow Duel:", mode)
