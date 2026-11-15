with open('backend/app/runtime/preview_server.py', 'r', encoding='utf-8') as f:
    text = f.read()

idx = text.find("def get_sky_strike_game_html")
idx2 = text.find("<canvas", idx)
print(text[idx2:idx2+200])
