import re

text = "sky strike sky strike is a fast-paced aerial combat game that pits players against each other in real-time dogfights. it offers dynamic weather, upgradeable aircraft, and cross-platform play to deliver an immersive and competitive experience. sky-strike-pzdm".lower()

words = ["shadow master", "shadowmaster", "shadow", "skill builder",
         "ninja", "stealth", "katana", "combat arena", "martial arts", "action game", "fighter"]

for w in words:
    escaped = re.escape(w.lower())
    pattern = r'(?:\b|_)' + escaped + r'(?:\b|_)'
    if re.search(pattern, text, re.IGNORECASE):
        print(f"MATCHED: '{w}' with pattern '{pattern}'")

# Also check all other archetypes in detect_project_archetype
