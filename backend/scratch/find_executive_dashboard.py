import sqlite3
import json

conn = sqlite3.connect('se_intelliplatform.db')
c = conn.cursor()

c.execute("select id, name, slug, settings from projects")
projects = c.fetchall()
print("=== ALL PROJECTS ===")
for p in projects:
    print(f"ID: {p[0]}, Name: {p[1]}, Slug: {p[2]}")

print("\n=== SEARCHING FOR EXECUTIVE / ANALYTICS ===")
target_pids = []
for p in projects:
    if "executive" in p[1].lower() or "analytic" in p[1].lower():
        target_pids.append(p)
        print(f"MATCH: {p[0]} - {p[1]} (settings: {p[3]})")

if not target_pids:
    print("No project with executive/analytic in name. Checking all recent projects:")
    c.execute("select id, name, created_at, settings from projects order by created_at desc limit 10")
    for row in c.fetchall():
        print(row)
else:
    for pid, name, slug, settings in target_pids:
        print(f"\n--- Project: {name} ({pid}) ---")
        c.execute("select id, title, created_at from assistant_conversations where project_id = ? order by created_at desc", (pid,))
        convs = c.fetchall()
        print(f"Conversations ({len(convs)}):")
        for conv in convs:
            print(f"  Conv ID: {conv[0]}, Title: {conv[1]}, Created: {conv[2]}")
            c.execute("select role, content, action_id, action_status, created_at from assistant_messages where conversation_id = ? order by created_at asc", (conv[0],))
            msgs = c.fetchall()
            print(f"  Messages ({len(msgs)}):")
            for m in msgs:
                role = m[0]
                content = m[1][:120].replace('\n', ' ')
                action = m[2]
                status = m[3]
                print(f"    [{role}] {content} | Action: {action} ({status})")

        c.execute("select id, version_number, status, source_reason, files_manifest, metadata from development_versions where project_id = ? order by version_number desc", (pid,))
        vers = c.fetchall()
        print(f"\nVersions ({len(vers)}):")
        for v in vers:
            print(f"  v{v[1]}: ID={v[0]}, Status={v[2]}, Reason={v[3]}")

conn.close()
