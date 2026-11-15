import urllib.request
import concurrent.futures
import time
import json
import sys

BASE_URL = "http://127.0.0.1:8001"

PROJECTS = {
    "sky_strike": {
        "id": "6ab754dc-c2bb-4689-9d87-2f69b778527f",
        "name": "Sky Strike",
        "expected_markers": ["skyStrikeCanvas", "Sky Strike", "dogfight"],
        "forbidden_markers": ["combatCanvas", "Katana Slash", "Shadow Master", "new-task-input", "spawnFood"]
    },
    "shadow_master": {
        "id": "b9a73557-04a6-4db5-9056-10884a2d5d53",
        "name": "Shadow Master",
        "expected_markers": ["combatCanvas", "Katana Slash", "Shadow Master"],
        "forbidden_markers": ["skyStrikeCanvas", "new-task-input", "spawnFood", "carromCanvas"]
    },
    "carrom_master": {
        "id": "657e9d2a-4dd2-4fe9-9bb7-20717c43b588",
        "name": "Carrom Master",
        "expected_markers": ["Carrom", "carromCanvas"],
        "forbidden_markers": ["combatCanvas", "skyStrikeCanvas", "new-task-input", "spawnFood"]
    }
}

def fetch_preview(project_id, extra_param=""):
    url = f"{BASE_URL}/preview/{project_id}{extra_param}"
    start = time.perf_counter()
    req = urllib.request.urlopen(url, timeout=5)
    duration_ms = (time.perf_counter() - start) * 1000
    html = req.read().decode("utf-8")
    return req.status, html, duration_ms

def test_individual_identities():
    print("================================================================================")
    print("TEST SUITE 1: AUTHORITATIVE PROJECT IDENTITY VERIFICATION")
    print("================================================================================")
    all_passed = True
    for key, spec in PROJECTS.items():
        status, html, dur = fetch_preview(spec["id"])
        print(f"\nEvaluating [{spec['name']}] (ID: {spec['id']}):")
        print(f"  HTTP Status: {status} in {dur:.2f}ms | HTML Length: {len(html)} bytes")
        
        # Check expected markers
        missing_expected = [m for m in spec["expected_markers"] if m.lower() not in html.lower()]
        if missing_expected:
            print(f"  ❌ FAILED: Missing expected markers: {missing_expected}")
            all_passed = False
        else:
            print(f"  ✅ All {len(spec['expected_markers'])} expected markers present: {spec['expected_markers']}")
            
        # Check forbidden markers
        found_forbidden = [m for m in spec["forbidden_markers"] if m.lower() in html.lower()]
        if found_forbidden:
            print(f"  ❌ FAILED: Cross-project collision detected! Forbidden markers: {found_forbidden}")
            all_passed = False
        else:
            print(f"  ✅ Zero cross-project leakage! No forbidden markers found: {spec['forbidden_markers']}")

    assert all_passed, "Test Suite 1 Failed: Project identity verification failed"
    print("\n>>> TEST SUITE 1 PASSED: All individual project identities verified.")

def test_stale_query_override_immunity():
    print("\n================================================================================")
    print("TEST SUITE 2: QUERY PARAMETER OVERRIDE IMMUNITY (ANTI-COLLISION)")
    print("================================================================================")
    sky_id = PROJECTS["sky_strike"]["id"]
    test_urls = [
        f"{BASE_URL}/?project_id={sky_id}&app=shadow_master",
        f"{BASE_URL}/preview?project_id={sky_id}&app=shadow_master",
        f"{BASE_URL}/preview/{sky_id}?app=shadow_master",
        f"{BASE_URL}/preview/{sky_id}?app=snake",
        f"{BASE_URL}/preview/{sky_id}?app=kanban"
    ]
    
    for u in test_urls:
        req = urllib.request.urlopen(u, timeout=5)
        html = req.read().decode("utf-8")
        assert "skyStrikeCanvas" in html, f"Failed URL immunity: {u} did not render Sky Strike canvas"
        assert "combatCanvas" not in html, f"Failed URL immunity: {u} leaked Shadow Master combatCanvas"
        assert "Katana Slash" not in html, f"Failed URL immunity: {u} leaked Katana Slash"
        print(f"  ✅ Protected against: {u}")
        
    print(">>> TEST SUITE 2 PASSED: URL query parameters cannot override authoritative project identity.")

def test_concurrent_rapid_switching():
    print("\n================================================================================")
    print("TEST SUITE 3: RAPID MULTI-PROJECT SWITCHING & CONCURRENCY ISOLATION")
    print("================================================================================")
    request_sequence = [
        ("sky_strike", PROJECTS["sky_strike"]["id"]),
        ("shadow_master", PROJECTS["shadow_master"]["id"]),
        ("carrom_master", PROJECTS["carrom_master"]["id"]),
        ("sky_strike", PROJECTS["sky_strike"]["id"]),
        ("carrom_master", PROJECTS["carrom_master"]["id"]),
        ("shadow_master", PROJECTS["shadow_master"]["id"]),
        ("sky_strike", PROJECTS["sky_strike"]["id"]),
        ("shadow_master", PROJECTS["shadow_master"]["id"]),
        ("carrom_master", PROJECTS["carrom_master"]["id"]),
    ]

    print(f"Executing {len(request_sequence)} concurrent requests across 3 distinct projects...")
    
    def worker(item):
        key, p_id = item
        status, html, dur = fetch_preview(p_id)
        spec = PROJECTS[key]
        for m in spec["expected_markers"]:
            if m.lower() not in html.lower():
                return False, f"[{key}] missing marker '{m}'"
        for m in spec["forbidden_markers"]:
            if m.lower() in html.lower():
                return False, f"[{key}] leaked forbidden marker '{m}'"
        return True, f"[{key}] verified cleanly in {dur:.2f}ms"

    with concurrent.futures.ThreadPoolExecutor(max_workers=5) as executor:
        results = list(executor.map(worker, request_sequence))

    for success, msg in results:
        print(f"  {'✅' if success else '❌'} {msg}")
        assert success, f"Concurrency isolation test failed: {msg}"

    print(">>> TEST SUITE 3 PASSED: Zero cross-project state pollution under rapid concurrent switching.")

if __name__ == "__main__":
    test_individual_identities()
    test_stale_query_override_immunity()
    test_concurrent_rapid_switching()
    print("\n================================================================================")
    print("ALL AUTOMATED VERIFICATION SUITES PASSED (100% SUCCESS)")
    print("================================================================================")
