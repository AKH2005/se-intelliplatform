import sys
sys.path.insert(0, "backend")

from app.agents.code_generation.archetypes import detect_project_archetype

tests = [
    ("Sky Strike", "Sky Strike is a fast-paced aerial combat game that pits players against each other in real-time dogfights.", "custom"),
    ("Shadow Master Skill Builder", "Interactive Ninja Combat Arena with Katana Slash and custom skill builder", "shadow_master"),
    ("Carrom Master", "Carrom board simulation with striker physics", "carrom"),
    ("Chess Master Pro", "Strategic chess game with 64 squares", "chess"),
    ("Arcade Snake", "Retro 2D snake arcade game", "snake_game"),
    ("Turbo Nitro Racing", "High-speed circuit racing game", "racing"),
    ("Tile Shift Puzzle", "Sliding 15 puzzle game", "puzzle"),
    ("MediCare Clinic", "Medical health portal and patient records", "custom"),
    ("Galactic Space Battle", "Space shooter dogfight arcade game", "custom"),
]

all_passed = True
for name, desc, expected in tests:
    res = detect_project_archetype(name=name, desc=desc)
    status = "PASS" if res == expected else "FAIL"
    print(f"[{status}] '{name}' => '{res}' (expected '{expected}')")
    if res != expected:
        all_passed = False

if all_passed:
    print("\nALL CLASSIFICATION TESTS PASSED 100%!")
else:
    print("\nSOME TESTS FAILED!")
    exit(1)
