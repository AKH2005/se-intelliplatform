import sys
import os

sys.path.insert(0, os.path.abspath("backend"))

from app.runtime.preview_server import get_custom_interactive_html

test_cases = [
    {
        "name": "Medical Application",
        "title": "MediHealth Clinic",
        "desc": "Medical records, doctor consultation schedules, and prescription tracking",
        "expected": ["CLINICAL HEALTHCARE", "Patient", "Admit", "Diagnosis"],
        "unexpected": ["Active Developers", "System Load", "Cyber Dreams", "Chef's Featured Menu"],
    },
    {
        "name": "Music Player",
        "title": "BeatWave Music Player",
        "desc": "An interactive web music player with playlists and audio controls",
        "expected": ["MUSIC & AUDIO PLAYER", "Midnight Neon", "Synthetix", "Track Playlist"],
        "unexpected": ["Patient", "Truffle Burger", "Bed Occupancy", "Active Developers"],
    },
    {
        "name": "Food Delivery Application",
        "title": "QuickBite Express",
        "desc": "Food delivery and restaurant menu ordering app",
        "expected": ["GOURMET FOOD DELIVERY", "Chef's Featured Menu", "Truffle Burger", "Your Cart & Order"],
        "unexpected": ["Patient", "Doctor", "Midnight Neon", "Bed Occupancy"],
    },
    {
        "name": "Learning Management System",
        "title": "AcademyCore LMS",
        "desc": "Online course learning management system with student curriculum and grading",
        "expected": ["LEARNING MANAGEMENT SYSTEM", "Enrolled Courses", "Active Course Curriculum", "Resume Lesson"],
        "unexpected": ["Truffle Burger", "Midnight Neon", "Patient", "Bed Occupancy"],
    },
    {
        "name": "Universal Domain",
        "title": "Quantum Inventory Hub",
        "desc": "Warehouse inventory tracking and asset lifecycle manager",
        "expected": ["DOMAIN APPLICATION PLATFORM", "Quantum Inventory Hub", "Managed Records"],
        "unexpected": ["Active Developers", "Trigger Primary Action", "Interactive Application Playground"],
    }
]

all_passed = True
for tc in test_cases:
    html = get_custom_interactive_html(title=tc["title"], desc=tc["desc"])
    missing = [exp for exp in tc["expected"] if exp.lower() not in html.lower()]
    found_unexpected = [unexp for unexp in tc["unexpected"] if unexp.lower() in html.lower()]

    if not missing and not found_unexpected:
        print(f"PASS: {tc['name']} -> Correctly synthesized with expected domain components!")
    else:
        print(f"FAIL: {tc['name']}")
        if missing:
            print(f"   Missing expected: {missing}")
        if found_unexpected:
            print(f"   Found unexpected: {found_unexpected}")
        all_passed = False

if all_passed:
    print("\nALL CUSTOM DOMAIN SYNTHESIZER TESTS PASSED 100%!")
else:
    sys.exit(1)
