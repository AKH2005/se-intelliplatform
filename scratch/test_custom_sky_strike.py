import sys
sys.path.insert(0, "backend")

from app.runtime.preview_server import get_custom_interactive_html

h = get_custom_interactive_html("Sky Strike", "Fast-paced aerial combat game with real-time dogfights")
print("Length:", len(h))
print("Contains 'Sky Strike':", "Sky Strike" in h)
print("Contains 'skyStrikeCanvas':", "skyStrikeCanvas" in h)
print("Contains 'dogfight':", "DOGFIGHT" in h)
print("Contains 'Managed Records' (should be False):", "Managed Records" in h)
print("Contains 'combatCanvas' (should be False):", "combatCanvas" in h)
