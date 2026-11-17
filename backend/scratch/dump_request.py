import json

with open(r'C:\Users\DELL\.gemini\antigravity\brain\3ff4955b-2849-4bb9-bc69-ab8ba87f7a5c\.system_generated\logs\transcript_full.jsonl', 'r', encoding='utf-8') as f:
    for line in f:
        data = json.loads(line)
        if data.get('step_index') == 16962:
            with open('backend/scratch/user_request_10.txt', 'w', encoding='utf-8') as out:
                out.write(data.get('content', ''))
            print("Wrote user request 10")
            break
