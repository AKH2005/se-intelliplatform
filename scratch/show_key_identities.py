import json

data = json.load(open("scratch/source_identity_audit.json", encoding="utf-8"))
targets = ["Shadow Master", "Carrom", "Executive Analytics", "TaskFlow", "EventHub", "Snake"]

found = []
seen_pids = set()
for d in data:
    for t in targets:
        if t.lower() in d["project_name"].lower() and d["project_id"] not in seen_pids:
            found.append(d)
            seen_pids.add(d["project_id"])
            break

print(json.dumps(found, indent=2))
