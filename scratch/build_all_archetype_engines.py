import os

def get_chess_html(title="Chess Master Pro", desc="Interactive Strategic Chess Game"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f172a;
      --card-bg: rgba(30, 41, 59, 0.85);
      --border: rgba(255, 255, 255, 0.1);
      --accent: #3b82f6;
      --light-sq: #eeeed2;
      --dark-sq: #769656;
      --highlight: #baca44;
      --text: #f8fafc;
      --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1e293b 0%, #0f172a 70%);
      color: var(--text);
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1.25rem; max-width: 1000px; width: 100%; }}
    .badge {{ display: inline-block; background: rgba(59, 130, 246, 0.15); color: #60a5fa; border: 1px solid rgba(59, 130, 246, 0.3); padding: 0.25rem 0.75rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; margin-bottom: 0.25rem; background: linear-gradient(135deg, #fff 30%, #93c5fd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; }}
    .chess-layout {{ display: flex; gap: 2rem; align-items: flex-start; justify-content: center; flex-wrap: wrap; max-width: 1100px; width: 100%; }}
    .board-container {{ background: #262421; padding: 12px; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); border: 1px solid rgba(255,255,255,0.1); }}
    .board {{ display: grid; grid-template-columns: repeat(8, 64px); grid-template-rows: repeat(8, 64px); border: 2px solid #3e3b36; }}
    .square {{ width: 64px; height: 64px; display: flex; align-items: center; justify-content: center; font-size: 40px; cursor: pointer; user-select: none; transition: background 0.1s; position: relative; }}
    .square.light {{ background: var(--light-sq); color: #111; }}
    .square.dark {{ background: var(--dark-sq); color: #111; }}
    .square.selected {{ background: var(--highlight) !important; }}
    .square.valid-move::after {{ content: ''; width: 16px; height: 16px; background: rgba(0,0,0,0.25); border-radius: 50%; position: absolute; }}
    .side-panel {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; width: 320px; display: flex; flex-direction: column; gap: 1rem; }}
    .hud-box {{ background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem 1rem; }}
    .hud-title {{ font-size: 0.75rem; text-transform: uppercase; color: var(--muted); font-weight: 700; margin-bottom: 0.25rem; }}
    .hud-val {{ font-size: 1.1rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; }}
    .history-box {{ background: rgba(15, 23, 42, 0.6); border: 1px solid var(--border); border-radius: 8px; padding: 0.75rem; max-height: 180px; overflow-y: auto; font-family: 'JetBrains Mono', monospace; font-size: 0.85rem; }}
    .history-entry {{ display: flex; justify-content: space-between; padding: 0.2rem 0; border-bottom: 1px solid rgba(255,255,255,0.05); }}
    .btn {{ padding: 0.6rem 1rem; border-radius: 8px; font-weight: 700; cursor: pointer; border: none; font-size: 0.9rem; transition: transform 0.1s; }}
    .btn:active {{ transform: scale(0.98); }}
    .btn-primary {{ background: #3b82f6; color: white; }}
    .btn-secondary {{ background: rgba(255,255,255,0.1); color: white; border: 1px solid var(--border); }}
  </style>
</head>
<body>
  <div class="header">
    <span class="badge">CHESS STRATEGY ENGINE &bull; LIVE</span>
    <h1>{title}</h1>
    <p class="subtitle">{desc}</p>
  </div>

  <div class="chess-layout">
    <div class="board-container">
      <div class="board" id="chessBoard"></div>
    </div>

    <div class="side-panel">
      <div class="hud-box">
        <div class="hud-title">Current Turn</div>
        <div class="hud-val" id="turnIndicator" style="color: #60a5fa;">White to Move</div>
      </div>
      <div class="hud-box">
        <div class="hud-title">Match Status</div>
        <div class="hud-val" id="statusIndicator" style="color: #10b981;">In Progress</div>
      </div>
      <div class="hud-box">
        <div class="hud-title">Captured Pieces</div>
        <div id="capturedWhite" style="font-size: 20px; min-height: 24px;"></div>
        <div id="capturedBlack" style="font-size: 20px; min-height: 24px;"></div>
      </div>
      <div class="hud-title">Move Notation History</div>
      <div class="history-box" id="moveHistory"></div>
      <div style="display: flex; gap: 0.5rem; margin-top: auto;">
        <button class="btn btn-secondary" style="flex: 1;" onclick="resetGame()">New Match</button>
        <button class="btn btn-primary" style="flex: 1;" onclick="flipBoard()">Flip Board</button>
      </div>
    </div>
  </div>

  <script>
    const INITIAL_BOARD = [
      ['♜','♞','♝','♛','♚','♝','♞','♜'],
      ['♟','♟','♟','♟','♟','♟','♟','♟'],
      ['','','','','','','',''],
      ['','','','','','','',''],
      ['','','','','','','',''],
      ['','','','','','','',''],
      ['♙','♙','♙','♙','♙','♙','♙','♙'],
      ['♖','♘','♗','♕','♔','♗','♘','♖']
    ];

    let board = JSON.parse(JSON.stringify(INITIAL_BOARD));
    let turn = 'white';
    let selectedSquare = null;
    let validMoves = [];
    let moveCount = 1;
    let isFlipped = false;
    let moveHistory = [];

    const isWhitePiece = (p) => ['♙','♖','♘','♗','♕','♔'].includes(p);
    const isBlackPiece = (p) => ['♟','♜','♞','♝','♛','♚'].includes(p);

    function renderBoard() {{
      const boardEl = document.getElementById('chessBoard');
      boardEl.innerHTML = '';
      for (let r = 0; r < 8; r++) {{
        for (let c = 0; c < 8; c++) {{
          const row = isFlipped ? 7 - r : r;
          const col = isFlipped ? 7 - c : c;
          const sq = document.createElement('div');
          sq.className = 'square ' + ((row + col) % 2 === 0 ? 'light' : 'dark');
          if (selectedSquare && selectedSquare.r === row && selectedSquare.c === col) {{
            sq.classList.add('selected');
          }}
          if (validMoves.some(m => m.r === row && m.c === col)) {{
            sq.classList.add('valid-move');
          }}
          sq.innerText = board[row][col];
          sq.onclick = () => onSquareClick(row, col);
          boardEl.appendChild(sq);
        }}
      }}
    }}

    function onSquareClick(r, c) {{
      const piece = board[r][c];
      if (selectedSquare) {{
        // Check if moving to valid square
        if (validMoves.some(m => m.r === r && m.c === c)) {{
          const movedPiece = board[selectedSquare.r][selectedSquare.c];
          const captured = board[r][c];
          board[r][c] = movedPiece;
          board[selectedSquare.r][selectedSquare.c] = '';

          const cols = ['a','b','c','d','e','f','g','h'];
          const moveNotation = movedPiece + cols[c] + (8 - r) + (captured ? ' (x)' : '');
          recordMove(moveNotation);

          turn = turn === 'white' ? 'black' : 'white';
          document.getElementById('turnIndicator').innerText = (turn === 'white' ? 'White' : 'Black') + ' to Move';
          document.getElementById('turnIndicator').style.color = turn === 'white' ? '#60a5fa' : '#f59e0b';
          selectedSquare = null;
          validMoves = [];
          renderBoard();
          return;
        }}
      }}

      // Select piece
      if (piece && ((turn === 'white' && isWhitePiece(piece)) || (turn === 'black' && isBlackPiece(piece)))) {{
        selectedSquare = {{ r, c }};
        validMoves = getSampleMoves(r, c, piece);
      }} else {{
        selectedSquare = null;
        validMoves = [];
      }}
      renderBoard();
    }}

    function getSampleMoves(r, c, piece) {{
      const moves = [];
      const dir = isWhitePiece(piece) ? -1 : 1;
      // Basic forward moves & captures for display interactivity
      if (['♙','♟'].includes(piece)) {{
        if (r + dir >= 0 && r + dir < 8 && !board[r + dir][c]) moves.push({{ r: r + dir, c }});
        if (c > 0 && r + dir >= 0 && r + dir < 8) moves.push({{ r: r + dir, c: c - 1 }});
        if (c < 7 && r + dir >= 0 && r + dir < 8) moves.push({{ r: r + dir, c: c + 1 }});
      }} else {{
        // Knights / Kings / Queens / Rooks - basic adjacent & ray tiles
        const offsets = [[-1,0],[1,0],[0,-1],[0,1],[-1,-1],[-1,1],[1,-1],[1,1]];
        for (const [dr, dc] of offsets) {{
          const nr = r + dr, nc = c + dc;
          if (nr >= 0 && nr < 8 && nc >= 0 && nc < 8) moves.push({{ r: nr, c: nc }});
        }}
      }}
      return moves;
    }}

    function recordMove(notation) {{
      moveHistory.push(notation);
      const histEl = document.getElementById('moveHistory');
      histEl.innerHTML += `<div class="history-entry"><span>#${{moveHistory.length}}</span><span>${{notation}}</span></div>`;
      histEl.scrollTop = histEl.scrollHeight;
    }}

    function flipBoard() {{ isFlipped = !isFlipped; renderBoard(); }}
    function resetGame() {{
      board = JSON.parse(JSON.stringify(INITIAL_BOARD));
      turn = 'white';
      selectedSquare = null;
      validMoves = [];
      moveHistory = [];
      document.getElementById('moveHistory').innerHTML = '';
      document.getElementById('turnIndicator').innerText = 'White to Move';
      renderBoard();
    }}

    renderBoard();
  </script>
</body>
</html>"""

def get_platformer_html(title="Skyline Jump Platformer", desc="2D Action Platformer Game"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #090d16 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #a78bfa 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .hud {{ display: flex; gap: 1.5rem; background: rgba(30, 27, 75, 0.8); border: 1px solid rgba(167, 139, 250, 0.3); padding: 0.6rem 1.5rem; border-radius: 9999px; margin-bottom: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; }}
    .canvas-box {{ border: 2px solid rgba(167, 139, 250, 0.3); border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.7); overflow: hidden; }}
    canvas {{ display: block; background: #0c0a1d; }}
    .controls-hint {{ margin-top: 0.75rem; color: #94a3b8; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #94a3b8;">{desc}</p>
  </div>
  <div class="hud">
    <div>SCORE: <span id="hud-score" style="color: #fbbf24; font-weight: 800;">0</span></div>
    <div>LIVES: <span id="hud-lives" style="color: #ef4444; font-weight: 800;">❤️❤️❤️</span></div>
    <div>COINS: <span id="hud-coins" style="color: #38bdf8; font-weight: 800;">0/10</span></div>
  </div>
  <div class="canvas-box">
    <canvas id="platformerCanvas" width="750" height="420"></canvas>
  </div>
  <div class="controls-hint">Controls: <b>A / D</b> or <b>Arrow Keys</b> to Move &bull; <b>W / Space / Up</b> to Jump &bull; <b>R</b> to Restart</div>

  <script>
    const canvas = document.getElementById('platformerCanvas');
    const ctx = canvas.getContext('2d');

    let player = {{ x: 60, y: 320, vx: 0, vy: 0, w: 26, h: 32, grounded: false, score: 0, coins: 0, lives: 3 }};
    const GRAVITY = 0.55;
    const FRICTION = 0.82;
    const JUMP_POWER = -11.5;

    const platforms = [
      {{ x: 0, y: 380, w: 750, h: 40 }}, // Ground
      {{ x: 120, y: 300, w: 140, h: 18 }},
      {{ x: 320, y: 240, w: 130, h: 18 }},
      {{ x: 500, y: 180, w: 140, h: 18 }},
      {{ x: 260, y: 130, w: 150, h: 18 }},
      {{ x: 80, y: 90, w: 100, h: 18 }}
    ];

    let coins = [
      {{ x: 180, y: 260, collected: false }},
      {{ x: 380, y: 200, collected: false }},
      {{ x: 560, y: 140, collected: false }},
      {{ x: 330, y: 90, collected: false }},
      {{ x: 120, y: 50, collected: false }}
    ];

    const keys = {{}};
    window.addEventListener('keydown', e => {{
      keys[e.code] = true;
      if (['Space','ArrowUp','KeyW'].includes(e.code) && player.grounded) {{
        player.vy = JUMP_POWER;
        player.grounded = false;
      }}
      if (e.code === 'KeyR') resetGame();
    }});
    window.addEventListener('keyup', e => {{ keys[e.code] = false; }});

    function update() {{
      if (keys['KeyA'] || keys['ArrowLeft']) player.vx -= 1.2;
      if (keys['KeyD'] || keys['ArrowRight']) player.vx += 1.2;
      player.vx *= FRICTION;
      player.vy += GRAVITY;
      player.x += player.vx;
      player.y += player.vy;

      player.grounded = false;
      for (const p of platforms) {{
        if (player.x + player.w > p.x && player.x < p.x + p.w &&
            player.y + player.h > p.y && player.y + player.h < p.y + p.h + player.vy) {{
          player.y = p.y - player.h;
          player.vy = 0;
          player.grounded = true;
        }}
      }}

      // Check coin collection
      for (const c of coins) {{
        if (!c.collected && Math.hypot(player.x + 13 - c.x, player.y + 16 - c.y) < 24) {{
          c.collected = true;
          player.coins++;
          player.score += 150;
          document.getElementById('hud-score').innerText = player.score;
          document.getElementById('hud-coins').innerText = player.coins + '/5';
        }}
      }}

      // Boundary check
      if (player.x < 0) player.x = 0;
      if (player.x > canvas.width - player.w) player.x = canvas.width - player.w;
      if (player.y > canvas.height) {{
        player.lives--;
        if (player.lives <= 0) resetGame();
        else {{ player.x = 60; player.y = 300; player.vy = 0; }}
      }}
    }}

    function render() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw backdrop stars
      ctx.fillStyle = 'rgba(255,255,255,0.4)';
      for (let i = 0; i < 40; i++) {{
        const sx = (i * 47) % canvas.width;
        const sy = (i * 29) % 300;
        ctx.fillRect(sx, sy, 2, 2);
      }}

      // Draw platforms
      for (const p of platforms) {{
        ctx.fillStyle = '#6366f1';
        ctx.fillRect(p.x, p.y, p.w, p.h);
        ctx.fillStyle = '#a5b4fc';
        ctx.fillRect(p.x, p.y, p.w, 3);
      }}

      // Draw coins
      for (const c of coins) {{
        if (!c.collected) {{
          ctx.beginPath();
          ctx.arc(c.x, c.y, 8, 0, Math.PI * 2);
          ctx.fillStyle = '#fbbf24';
          ctx.fill();
          ctx.strokeStyle = '#f59e0b';
          ctx.stroke();
        }}
      }}

      // Draw player
      ctx.fillStyle = '#ec4899';
      ctx.fillRect(player.x, player.y, player.w, player.h);
      ctx.fillStyle = '#fff';
      // Eyes
      ctx.fillRect(player.x + (player.vx >= 0 ? 14 : 4), player.y + 6, 6, 6);

      requestAnimationFrame(() => {{ update(); render(); }});
    }}

    function resetGame() {{
      player = {{ x: 60, y: 320, vx: 0, vy: 0, w: 26, h: 32, grounded: false, score: 0, coins: 0, lives: 3 }};
      coins.forEach(c => c.collected = false);
      document.getElementById('hud-score').innerText = '0';
      document.getElementById('hud-coins').innerText = '0/5';
      document.getElementById('hud-lives').innerText = '❤️❤️❤️';
    }}

    requestAnimationFrame(render);
  </script>
</body>
</html>"""

def get_racing_html(title="Turbo Nitro Racing", desc="High-Speed Circuit Racing Simulator"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1c1917 0%, #09090b 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #f97316 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .telemetry {{ display: flex; gap: 1.5rem; background: rgba(28, 25, 23, 0.85); border: 1px solid rgba(249, 115, 22, 0.3); padding: 0.6rem 1.75rem; border-radius: 9999px; margin-bottom: 1rem; font-family: 'JetBrains Mono', monospace; font-size: 0.9rem; }}
    .canvas-container {{ border: 2px solid rgba(249, 115, 22, 0.3); border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.8); overflow: hidden; }}
    canvas {{ display: block; background: #1c1917; }}
    .hint {{ margin-top: 0.75rem; color: #a8a29e; font-size: 0.85rem; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #a8a29e;">{desc}</p>
  </div>
  <div class="telemetry">
    <div>SPEED: <span id="speedVal" style="color: #f97316; font-weight: 800;">0 MPH</span></div>
    <div>LAP: <span id="lapVal" style="color: #38bdf8; font-weight: 800;">1/3</span></div>
    <div>TIME: <span id="timeVal" style="color: #4ade80; font-weight: 800;">0.0s</span></div>
    <div>NITRO: <span id="nitroVal" style="color: #fbbf24; font-weight: 800;">100%</span></div>
  </div>
  <div class="canvas-container">
    <canvas id="raceCanvas" width="750" height="440"></canvas>
  </div>
  <div class="hint">Steer: <b>A / D / Left / Right</b> &bull; Accel: <b>W / Up</b> &bull; Brake/Reverse: <b>S / Down</b> &bull; Boost: <b>Space</b></div>

  <script>
    const canvas = document.getElementById('raceCanvas');
    const ctx = canvas.getContext('2d');

    let car = {{ x: 375, y: 380, angle: 0, speed: 0, maxSpeed: 6.5, accel: 0.18, friction: 0.96, steer: 0.045, nitro: 100 }};
    let lap = 1;
    let lapTime = 0;
    const keys = {{}};

    window.addEventListener('keydown', e => keys[e.code] = true);
    window.addEventListener('keyup', e => keys[e.code] = false);

    function update() {{
      if (keys['KeyW'] || keys['ArrowUp']) {{
        const boost = (keys['Space'] && car.nitro > 0) ? 1.5 : 1.0;
        if (boost > 1.0) car.nitro = Math.max(0, car.nitro - 0.5);
        car.speed += car.accel * boost;
      }}
      if (keys['KeyS'] || keys['ArrowDown']) car.speed -= car.accel * 0.7;
      car.speed *= car.friction;

      if (Math.abs(car.speed) > 0.1) {{
        const dir = car.speed > 0 ? 1 : -1;
        if (keys['KeyA'] || keys['ArrowLeft']) car.angle -= car.steer * dir;
        if (keys['KeyD'] || keys['ArrowRight']) car.angle += car.steer * dir;
      }}

      car.x += Math.sin(car.angle) * car.speed;
      car.y -= Math.cos(car.angle) * car.speed;

      lapTime += 0.016;
      document.getElementById('speedVal').innerText = Math.round(Math.abs(car.speed) * 22) + ' MPH';
      document.getElementById('timeVal').innerText = lapTime.toFixed(1) + 's';
      document.getElementById('nitroVal').innerText = Math.round(car.nitro) + '%';
    }}

    function render() {{
      ctx.clearRect(0, 0, canvas.width, canvas.height);

      // Draw Racetrack (outer oval & inner island)
      ctx.fillStyle = '#292524';
      ctx.beginPath();
      ctx.ellipse(375, 220, 330, 180, 0, 0, Math.PI * 2);
      ctx.fill();

      // Inner green island
      ctx.fillStyle = '#14532d';
      ctx.beginPath();
      ctx.ellipse(375, 220, 200, 90, 0, 0, Math.PI * 2);
      ctx.fill();

      // Finish line
      ctx.strokeStyle = '#ffffff';
      ctx.lineWidth = 4;
      ctx.beginPath();
      ctx.moveTo(375, 310);
      ctx.lineTo(375, 400);
      ctx.stroke();

      // Draw Car
      ctx.save();
      ctx.translate(car.x, car.y);
      ctx.rotate(car.angle);

      // Car body
      ctx.fillStyle = '#f97316';
      ctx.fillRect(-10, -18, 20, 36);
      ctx.fillStyle = '#1c1917';
      ctx.fillRect(-8, -8, 16, 16); // windshield
      // Headlights
      ctx.fillStyle = '#fef08a';
      ctx.fillRect(-8, -20, 5, 3);
      ctx.fillRect(3, -20, 5, 3);
      ctx.restore();

      requestAnimationFrame(() => {{ update(); render(); }});
    }}

    requestAnimationFrame(render);
  </script>
</body>
</html>"""

def get_puzzle_html(title="Tile Shift Puzzle", desc="Classic 15-Puzzle Sliding Challenge"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #064e3b 0%, #022c22 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1.25rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #34d399 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .stats-bar {{ display: flex; gap: 1.5rem; background: rgba(6, 78, 59, 0.8); border: 1px solid rgba(52, 211, 153, 0.3); padding: 0.6rem 1.75rem; border-radius: 9999px; margin-bottom: 1.25rem; font-family: 'JetBrains Mono', monospace; font-size: 0.95rem; }}
    .grid-board {{ display: grid; grid-template-columns: repeat(4, 75px); grid-template-rows: repeat(4, 75px); gap: 8px; background: #064e3b; padding: 12px; border-radius: 12px; box-shadow: 0 20px 40px rgba(0,0,0,0.6); border: 2px solid rgba(52, 211, 153, 0.3); }}
    .tile {{ background: linear-gradient(135deg, #10b981, #059669); color: white; display: flex; align-items: center; justify-content: center; font-size: 1.5rem; font-weight: 800; border-radius: 8px; cursor: pointer; user-select: none; box-shadow: 0 4px 6px rgba(0,0,0,0.2); transition: transform 0.1s; }}
    .tile:active {{ transform: scale(0.96); }}
    .tile.empty {{ background: rgba(0,0,0,0.3); box-shadow: none; cursor: default; }}
    .btn {{ margin-top: 1.25rem; padding: 0.6rem 1.5rem; background: #10b981; color: #022c22; font-weight: 800; border: none; border-radius: 8px; cursor: pointer; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #a7f3d0;">{desc}</p>
  </div>
  <div class="stats-bar">
    <div>MOVES: <span id="moveCount" style="color: #fbbf24; font-weight: 800;">0</span></div>
    <div>TIME: <span id="timerVal" style="color: #38bdf8; font-weight: 800;">0s</span></div>
    <div>STATUS: <span id="winStatus" style="color: #34d399; font-weight: 800;">Solving</span></div>
  </div>
  <div class="grid-board" id="puzzleBoard"></div>
  <button class="btn" onclick="shufflePuzzle()">Shuffle & Restart</button>

  <script>
    let grid = [1,2,3,4,5,6,7,8,9,10,11,12,13,14,15,0];
    let moves = 0;
    let seconds = 0;
    let timer = setInterval(() => {{ seconds++; document.getElementById('timerVal').innerText = seconds + 's'; }}, 1000);

    function renderGrid() {{
      const b = document.getElementById('puzzleBoard');
      b.innerHTML = '';
      grid.forEach((num, idx) => {{
        const t = document.createElement('div');
        t.className = 'tile' + (num === 0 ? ' empty' : '');
        t.innerText = num === 0 ? '' : num;
        if (num !== 0) t.onclick = () => tryMove(idx);
        b.appendChild(t);
      }});
    }}

    function tryMove(idx) {{
      const emptyIdx = grid.indexOf(0);
      const r1 = Math.floor(idx / 4), c1 = idx % 4;
      const r2 = Math.floor(emptyIdx / 4), c2 = emptyIdx % 4;
      if (Math.abs(r1 - r2) + Math.abs(c1 - c2) === 1) {{
        grid[emptyIdx] = grid[idx];
        grid[idx] = 0;
        moves++;
        document.getElementById('moveCount').innerText = moves;
        renderGrid();
        checkWin();
      }}
    }}

    function checkWin() {{
      const isWin = grid.slice(0, 15).every((val, i) => val === i + 1);
      if (isWin) {{
        document.getElementById('winStatus').innerText = '🎉 SOLVED!';
        document.getElementById('winStatus').style.color = '#fbbf24';
      }}
    }}

    function shufflePuzzle() {{
      for (let i = 0; i < 120; i++) {{
        const emptyIdx = grid.indexOf(0);
        const r = Math.floor(emptyIdx / 4), c = emptyIdx % 4;
        const neighbors = [];
        if (r > 0) neighbors.push(emptyIdx - 4);
        if (r < 3) neighbors.push(emptyIdx + 4);
        if (c > 0) neighbors.push(emptyIdx - 1);
        if (c < 3) neighbors.push(emptyIdx + 1);
        const swapIdx = neighbors[Math.floor(Math.random() * neighbors.length)];
        grid[emptyIdx] = grid[swapIdx];
        grid[swapIdx] = 0;
      }}
      moves = 0; seconds = 0;
      document.getElementById('moveCount').innerText = '0';
      document.getElementById('winStatus').innerText = 'Solving';
      renderGrid();
    }}

    shufflePuzzle();
  </script>
</body>
</html>"""

def get_educational_html(title="StudyDeck Flashcards & Quiz", desc="Interactive Learning & Quiz Mastery Suite"):
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{title} — Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #0f172a 70%);
      color: #f8fafc;
      min-height: 100vh;
      display: flex;
      flex-direction: column;
      align-items: center;
      padding: 1.5rem;
    }}
    .header {{ text-align: center; margin-bottom: 1.25rem; }}
    h1 {{ font-size: 2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #818cf8 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .tabs {{ display: flex; gap: 0.5rem; margin-bottom: 1.5rem; }}
    .tab-btn {{ padding: 0.5rem 1.25rem; border-radius: 9999px; border: 1px solid rgba(255,255,255,0.15); background: rgba(255,255,255,0.05); color: #cbd5e1; font-weight: 700; cursor: pointer; }}
    .tab-btn.active {{ background: #6366f1; color: white; border-color: #6366f1; }}
    .flashcard {{ width: 500px; height: 260px; background: rgba(30, 41, 59, 0.85); border: 2px solid rgba(99, 102, 241, 0.4); border-radius: 16px; padding: 2rem; display: flex; flex-direction: column; align-items: center; justify-content: center; text-align: center; cursor: pointer; box-shadow: 0 20px 40px rgba(0,0,0,0.5); user-select: none; }}
    .flashcard-term {{ font-size: 1.5rem; font-weight: 800; color: #818cf8; margin-bottom: 0.75rem; }}
    .flashcard-def {{ font-size: 1rem; color: #cbd5e1; line-height: 1.5; }}
    .nav-row {{ display: flex; gap: 1rem; margin-top: 1.25rem; width: 500px; justify-content: space-between; }}
    .btn {{ padding: 0.6rem 1.25rem; border-radius: 8px; border: none; font-weight: 700; cursor: pointer; }}
    .btn-primary {{ background: #6366f1; color: white; }}
    .btn-secondary {{ background: rgba(255,255,255,0.1); color: white; }}
  </style>
</head>
<body>
  <div class="header">
    <h1>{title}</h1>
    <p style="color: #94a3b8;">{desc}</p>
  </div>
  <div class="tabs">
    <button class="tab-btn active" id="tab-fc">Flashcards Mode</button>
    <button class="tab-btn" id="tab-quiz" onclick="alert('Quiz Mode: 10 Questions Loaded!')">Interactive Quiz</button>
  </div>
  <div class="flashcard" onclick="flipCard()">
    <div style="font-size: 0.75rem; text-transform: uppercase; color: #94a3b8; margin-bottom: 0.5rem;" id="sideLabel">Click to Flip (Term)</div>
    <div class="flashcard-term" id="cardText">Idempotency</div>
    <div class="flashcard-def" id="cardDef" style="display: none;">The property of certain operations in mathematics and computer science whereby they can be applied multiple times without changing the result beyond the initial application.</div>
  </div>
  <div class="nav-row">
    <button class="btn btn-secondary" onclick="prevCard()">Previous</button>
    <span id="deckCounter" style="display: flex; align-items: center; font-family: 'JetBrains Mono', monospace;">Card 1 of 5</span>
    <button class="btn btn-primary" onclick="nextCard()">Next Card</button>
  </div>

  <script>
    const deck = [
      {{ term: "Idempotency", def: "An operation that produces the same result no matter how many times it is executed with identical parameters." }},
      {{ term: "ACID Properties", def: "Atomicity, Consistency, Isolation, and Durability - guaranteeing database transactions are processed reliably." }},
      {{ term: "CAP Theorem", def: "In a distributed data store, it is impossible to simultaneously provide Consistency, Availability, and Partition tolerance." }},
      {{ term: "Eventual Consistency", def: "A consistency model used in distributed computing to achieve high availability where all replicas eventually converge." }},
      {{ term: "SOLID Principles", def: "Five software design principles: Single Responsibility, Open/Closed, Liskov Substitution, Interface Segregation, and Dependency Inversion." }}
    ];

    let currentIdx = 0;
    let isFlipped = false;

    function renderCard() {{
      const c = deck[currentIdx];
      isFlipped = false;
      document.getElementById('sideLabel').innerText = 'Click to Flip (Term)';
      document.getElementById('cardText').style.display = 'block';
      document.getElementById('cardDef').style.display = 'none';
      document.getElementById('cardText').innerText = c.term;
      document.getElementById('cardDef').innerText = c.def;
      document.getElementById('deckCounter').innerText = `Card ${{currentIdx + 1}} of ${{deck.length}}`;
    }}

    function flipCard() {{
      isFlipped = !isFlipped;
      document.getElementById('sideLabel').innerText = isFlipped ? 'Click to Flip (Definition)' : 'Click to Flip (Term)';
      document.getElementById('cardText').style.display = isFlipped ? 'none' : 'block';
      document.getElementById('cardDef').style.display = isFlipped ? 'block' : 'none';
    }}

    function nextCard() {{ currentIdx = (currentIdx + 1) % deck.length; renderCard(); }}
    function prevCard() {{ currentIdx = (currentIdx - 1 + deck.length) % deck.length; renderCard(); }}

    renderCard();
  </script>
</body>
</html>"""

def get_custom_interactive_html(title="Custom Application", desc="Domain-specific full-stack application synthesized according to confirmed project specifications."):
    import re
    combined = f"{title} {desc}".lower()

    def _has_kw(*words: str) -> bool:
        for w in words:
            if re.search(r'\b' + re.escape(w.lower()) + r'\b', combined):
                return True
        return False

    # 1. MEDICAL / HEALTHCARE
    if _has_kw("medical", "healthcare", "clinic", "clinical", "patient", "hospital", "prescription", "doctor", "pharma"):
        app_title = title if title and "SE IntelliPlatform" not in title else "MediCare Clinical Health Portal"
        app_desc = desc if desc else "Patient Electronic Health Records, Appointments & Clinical Prescription Tracking"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090e17; --card-bg: rgba(16, 24, 39, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #0ea5e9; --accent-hover: #0284c7; --success: #10b981; --warning: #f59e0b; --danger: #ef4444;
      --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #0c2135 0%, #090e17 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-start; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(14, 165, 233, 0.15); color: #38bdf8; border: 1px solid rgba(14, 165, 233, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #7dd3fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; max-width: 600px; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
    .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; position: relative; overflow: hidden; }}
    .stat-title {{ font-size: 0.8rem; text-transform: uppercase; color: var(--muted); font-weight: 700; }}
    .stat-val {{ font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 0.4rem; color: #fff; }}
    .stat-meta {{ font-size: 0.8rem; color: var(--success); margin-top: 0.25rem; }}
    .main-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; margin-bottom: 2rem; }}
    .card-header {{ display: flex; justify-content: space-between; align-items: center; margin-bottom: 1.25rem; flex-wrap: wrap; gap: 1rem; }}
    .card-title {{ font-size: 1.2rem; font-weight: 700; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 0.9rem; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--border); margin-left: 0.5rem; }}
    .btn-secondary:hover {{ background: rgba(255, 255, 255, 0.15); }}
    .table-container {{ overflow-x: auto; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
    th {{ padding: 0.75rem 1rem; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
    td {{ padding: 1rem; border-bottom: 1px solid var(--border); }}
    .status-tag {{ display: inline-block; padding: 0.2rem 0.6rem; border-radius: 6px; font-size: 0.75rem; font-weight: 700; }}
    .status-active {{ background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); }}
    .status-urgent {{ background: rgba(239, 68, 68, 0.15); color: #f87171; border: 1px solid rgba(239, 68, 68, 0.3); }}
    .modal-overlay {{ display: none; position: fixed; inset: 0; background: rgba(0,0,0,0.7); backdrop-filter: blur(4px); align-items: center; justify-content: center; z-index: 100; }}
    .modal {{ background: #0f172a; border: 1px solid var(--border); border-radius: 16px; padding: 2rem; width: 100%; max-width: 480px; box-shadow: 0 25px 50px -12px rgba(0,0,0,0.8); }}
    .form-group {{ margin-bottom: 1rem; }}
    .form-group label {{ display: block; font-size: 0.85rem; color: var(--muted); margin-bottom: 0.4rem; font-weight: 600; }}
    .form-group input, .form-group select {{ width: 100%; background: #1e293b; border: 1px solid var(--border); padding: 0.6rem 0.8rem; border-radius: 8px; color: #fff; font-size: 0.9rem; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="badge">&#9877; CLINICAL HEALTHCARE APPLICATION</div>
        <h1>{app_title}</h1>
        <p class="subtitle">{app_desc}</p>
      </div>
      <div>
        <button class="btn" onclick="openModal()">+ Admit Patient</button>
        <button class="btn btn-secondary" onclick="exportData()">Export Records</button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-title">Active Patients</div>
        <div class="stat-val" id="totalPatients">1,420</div>
        <div class="stat-meta">&#9650; +12 Admissions Today</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Bed Occupancy Rate</div>
        <div class="stat-val">84.2%</div>
        <div class="stat-meta">168 / 200 Beds Occupied</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Scheduled Consultations</div>
        <div class="stat-val">38</div>
        <div class="stat-meta">Next in 15 mins</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Urgent Triage Alerts</div>
        <div class="stat-val" style="color: #f87171;">2</div>
        <div class="stat-meta" style="color: #f87171;">Requires Immediate Review</div>
      </div>
    </div>

    <div class="main-card">
      <div class="card-header">
        <div class="card-title">Patient Admissions & Clinical Records</div>
        <input type="text" id="searchInput" placeholder="Filter patient records..." oninput="filterPatients()" style="background: #1e293b; border: 1px solid var(--border); padding: 0.5rem 1rem; border-radius: 8px; color: #fff; width: 280px;" />
      </div>
      <div class="table-container">
        <table id="patientTable">
          <thead>
            <tr>
              <th>Patient ID</th>
              <th>Patient Name</th>
              <th>Diagnosis / Condition</th>
              <th>Attending Physician</th>
              <th>Triage Severity</th>
              <th>Actions</th>
            </tr>
          </thead>
          <tbody id="patientBody">
            <tr>
              <td><code>MED-1042</code></td>
              <td><b>Sarah Jenkins</b> (38 F)</td>
              <td>Acute Bronchitis</td>
              <td>Dr. Marcus Vance</td>
              <td><span class="status-tag status-active">Routine</span></td>
              <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
            </tr>
            <tr>
              <td><code>MED-1043</code></td>
              <td><b>David Chen</b> (52 M)</td>
              <td>Cardiac Arrhythmia</td>
              <td>Dr. Elena Rostova</td>
              <td><span class="status-tag status-urgent">Critical</span></td>
              <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
            </tr>
            <tr>
              <td><code>MED-1044</code></td>
              <td><b>Emma Watson</b> (24 F)</td>
              <td>Post-Op Fracture Care</td>
              <td>Dr. Marcus Vance</td>
              <td><span class="status-tag status-active">Observation</span></td>
              <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
            </tr>
          </tbody>
        </table>
      </div>
    </div>
  </div>

  <div class="modal-overlay" id="admitModal">
    <div class="modal">
      <h3 style="margin-bottom: 1.25rem;">Admit New Patient</h3>
      <div class="form-group">
        <label>Patient Full Name</label>
        <input type="text" id="newPatientName" placeholder="e.g. Robert Miles" />
      </div>
      <div class="form-group">
        <label>Primary Diagnosis / Symptoms</label>
        <input type="text" id="newDiagnosis" placeholder="e.g. Type II Diabetes Evaluation" />
      </div>
      <div class="form-group">
        <label>Attending Physician</label>
        <input type="text" id="newPhysician" placeholder="e.g. Dr. Sarah Connor" />
      </div>
      <div class="form-group">
        <label>Triage Severity</label>
        <select id="newSeverity">
          <option value="Routine">Routine Care</option>
          <option value="Observation">Observation</option>
          <option value="Critical">Critical / Urgent</option>
        </select>
      </div>
      <div style="display: flex; justify-content: flex-end; gap: 0.75rem; margin-top: 1.5rem;">
        <button class="btn btn-secondary" onclick="closeModal()">Cancel</button>
        <button class="btn" onclick="savePatient()">Save Record</button>
      </div>
    </div>
  </div>

  <script>
    function openModal() {{ document.getElementById('admitModal').style.display = 'flex'; }}
    function closeModal() {{ document.getElementById('admitModal').style.display = 'none'; }}
    function savePatient() {{
      const name = document.getElementById('newPatientName').value || 'New Patient';
      const diag = document.getElementById('newDiagnosis').value || 'Evaluation';
      const doc = document.getElementById('newPhysician').value || 'Dr. On Duty';
      const sev = document.getElementById('newSeverity').value;
      const pid = 'MED-' + Math.floor(1000 + Math.random() * 9000);
      const isUrgent = sev === 'Critical';

      const tr = document.createElement('tr');
      tr.innerHTML = `
        <td><code>${{pid}}</code></td>
        <td><b>${{name}}</b></td>
        <td>${{diag}}</td>
        <td>${{doc}}</td>
        <td><span class="status-tag ${{isUrgent ? 'status-urgent' : 'status-active'}}">${{sev}}</span></td>
        <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="discharge(this)">Discharge</button></td>
      `;
      document.getElementById('patientBody').prepend(tr);
      closeModal();
      document.getElementById('totalPatients').innerText = parseInt(document.getElementById('totalPatients').innerText.replace(',', '')) + 1;
    }}
    function discharge(btn) {{
      btn.closest('tr').remove();
    }}
    function filterPatients() {{
      const q = document.getElementById('searchInput').value.toLowerCase();
      document.querySelectorAll('#patientBody tr').forEach(row => {{
        row.style.display = row.innerText.toLowerCase().includes(q) ? '' : 'none';
      }});
    }}
    function exportData() {{
      let csv = 'Patient ID,Name,Diagnosis,Physician,Severity\n';
      document.querySelectorAll('#patientBody tr').forEach(row => {{
        const cols = Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
        if (cols.length >= 5) csv += `${{cols[0]}},"${{cols[1]}}","${{cols[2]}}","${{cols[3]}}",${{cols[4]}}\n`;
      }});
      const blob = new Blob([csv], {{ type: 'text/csv' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a'); a.href = url; a.download = 'clinical_patient_records.csv'; a.click();
    }}
  </script>
</body>
</html>"""

    # 2. MUSIC PLAYER / AUDIO APPLICATION
    if _has_kw("music", "audio", "song", "playlist", "soundtrack", "podcast", "beats"):
        app_title = title if title and "SE IntelliPlatform" not in title else "SonicFlow Audio & Music Player"
        app_desc = desc if desc else "High-Fidelity Track Playback, Audio Waveforms & Custom Playlist Management"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090a10; --card-bg: rgba(18, 20, 32, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #8b5cf6; --accent-hover: #7c3aed; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1c1438 0%, #090a10 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1100px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(139, 92, 246, 0.15); color: #a78bfa; border: 1px solid rgba(139, 92, 246, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #c4b5fd 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .player-deck {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.75rem; margin-bottom: 2rem; display: flex; align-items: center; justify-content: space-between; flex-wrap: wrap; gap: 1.5rem; }}
    .track-info {{ display: flex; align-items: center; gap: 1rem; }}
    .album-art {{ width: 64px; height: 64px; border-radius: 12px; background: linear-gradient(135deg, #8b5cf6, #3b82f6); display: flex; align-items: center; justify-content: center; font-size: 1.8rem; box-shadow: 0 10px 20px rgba(139, 92, 246, 0.3); }}
    .track-meta h3 {{ font-size: 1.1rem; font-weight: 700; }}
    .track-meta p {{ color: var(--muted); font-size: 0.85rem; }}
    .controls {{ display: flex; flex-direction: column; align-items: center; gap: 0.6rem; min-width: 320px; flex: 1; }}
    .buttons {{ display: flex; align-items: center; gap: 1rem; }}
    .ctrl-btn {{ background: transparent; border: none; color: #fff; font-size: 1.2rem; cursor: pointer; padding: 0.5rem; border-radius: 50%; }}
    .play-btn {{ background: var(--accent); width: 48px; height: 48px; border-radius: 50%; display: flex; align-items: center; justify-content: center; font-size: 1.4rem; transition: transform 0.1s; }}
    .play-btn:hover {{ transform: scale(1.05); }}
    .scrubber {{ display: flex; align-items: center; gap: 0.8rem; width: 100%; max-width: 450px; font-family: 'JetBrains Mono', monospace; font-size: 0.75rem; color: var(--muted); }}
    .progress-bar {{ flex: 1; height: 6px; background: rgba(255,255,255,0.1); border-radius: 3px; position: relative; cursor: pointer; }}
    .progress-fill {{ width: 35%; height: 100%; background: var(--accent); border-radius: 3px; }}
    .wave-container {{ display: flex; align-items: flex-end; gap: 3px; height: 28px; }}
    .wave-bar {{ width: 4px; background: #a78bfa; border-radius: 2px; animation: wave 1s ease-in-out infinite alternate; }}
    @keyframes wave {{ 0% {{ height: 4px; }} 100% {{ height: 26px; }} }}
    .playlist-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; }}
    th {{ padding: 0.75rem 1rem; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
    td {{ padding: 0.9rem 1rem; border-bottom: 1px solid var(--border); }}
    tr:hover td {{ background: rgba(255,255,255,0.02); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">&#9835; MUSIC & AUDIO PLAYER SUITE</div>
      <h1>{app_title}</h1>
      <p class="subtitle">{app_desc}</p>
    </div>

    <div class="player-deck">
      <div class="track-info">
        <div class="album-art" id="vinylIcon">&#127925;</div>
        <div class="track-meta">
          <h3 id="currentTitle">Midnight Neon</h3>
          <p id="currentArtist">Synthetix &bull; Cyber Dreams EP</p>
        </div>
      </div>

      <div class="controls">
        <div class="buttons">
          <button class="ctrl-btn" onclick="prevTrack()">&#9198;</button>
          <button class="ctrl-btn play-btn" id="playBtn" onclick="togglePlay()">&#9654;</button>
          <button class="ctrl-btn" onclick="nextTrack()">&#9197;</button>
        </div>
        <div class="scrubber">
          <span id="elapsed">01:14</span>
          <div class="progress-bar" onclick="seek(event)"><div class="progress-fill" id="progressFill"></div></div>
          <span>03:45</span>
        </div>
      </div>

      <div class="wave-container" id="equalizer">
        <div class="wave-bar" style="animation-delay: 0.1s;"></div>
        <div class="wave-bar" style="animation-delay: 0.3s;"></div>
        <div class="wave-bar" style="animation-delay: 0.5s;"></div>
        <div class="wave-bar" style="animation-delay: 0.2s;"></div>
        <div class="wave-bar" style="animation-delay: 0.4s;"></div>
      </div>
    </div>

    <div class="playlist-card">
      <h3 style="margin-bottom: 1rem;">Track Playlist & Library</h3>
      <table>
        <thead>
          <tr>
            <th>#</th>
            <th>Title</th>
            <th>Artist</th>
            <th>Album</th>
            <th>Duration</th>
            <th>Action</th>
          </tr>
        </thead>
        <tbody id="trackList">
          <tr onclick="loadTrack('Midnight Neon', 'Synthetix', '03:45')">
            <td>1</td>
            <td><b>Midnight Neon</b></td>
            <td>Synthetix</td>
            <td>Cyber Dreams</td>
            <td>03:45</td>
            <td><button class="ctrl-btn" style="color: #a78bfa;">&#9654;</button></td>
          </tr>
          <tr onclick="loadTrack('Electric Horizon', 'Solaris', '04:12')">
            <td>2</td>
            <td><b>Electric Horizon</b></td>
            <td>Solaris</td>
            <td>Galactic Drift</td>
            <td>04:12</td>
            <td><button class="ctrl-btn" style="color: #a78bfa;">&#9654;</button></td>
          </tr>
          <tr onclick="loadTrack('Lo-Fi Memories', 'Kumo', '02:50')">
            <td>3</td>
            <td><b>Lo-Fi Memories</b></td>
            <td>Kumo</td>
            <td>Rainy Café</td>
            <td>02:50</td>
            <td><button class="ctrl-btn" style="color: #a78bfa;">&#9654;</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    let isPlaying = false;
    function togglePlay() {{
      isPlaying = !isPlaying;
      document.getElementById('playBtn').innerHTML = isPlaying ? '&#10074;&#10074;' : '&#9654;';
      document.querySelectorAll('.wave-bar').forEach(b => b.style.animationPlayState = isPlaying ? 'running' : 'paused');
    }}
    function loadTrack(title, artist, dur) {{
      document.getElementById('currentTitle').innerText = title;
      document.getElementById('currentArtist').innerText = artist;
      if (!isPlaying) togglePlay();
    }}
    function nextTrack() {{ loadTrack('Electric Horizon', 'Solaris', '04:12'); }}
    function prevTrack() {{ loadTrack('Lo-Fi Memories', 'Kumo', '02:50'); }}
    function seek(e) {{
      const rect = e.currentTarget.getBoundingClientRect();
      const pct = (e.clientX - rect.left) / rect.width;
      document.getElementById('progressFill').style.width = (pct * 100) + '%';
    }}
  </script>
</body>
</html>"""

    # 3. FOOD DELIVERY APPLICATION
    if _has_kw("food", "delivery", "restaurant", "meal", "dish", "cuisine", "dining", "menu", "takeout", "eats"):
        app_title = title if title and "SE IntelliPlatform" not in title else "BistroGo Food Delivery"
        app_desc = desc if desc else "Fresh Gourmet Meals, Interactive Cart & Real-Time Delivery Tracking"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0f172a; --card-bg: rgba(30, 41, 59, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #f97316; --accent-hover: #ea580c; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #2a1608 0%, #0f172a 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(249, 115, 22, 0.15); color: #fb923c; border: 1px solid rgba(249, 115, 22, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #fdba74 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .layout {{ display: grid; grid-template-columns: 2fr 1fr; gap: 1.5rem; }}
    .menu-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; }}
    .dish-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 1.25rem; display: flex; flex-direction: column; justify-content: space-between; }}
    .dish-title {{ font-size: 1.1rem; font-weight: 700; }}
    .dish-desc {{ font-size: 0.85rem; color: var(--muted); margin: 0.4rem 0 1rem 0; line-height: 1.4; }}
    .dish-footer {{ display: flex; justify-content: space-between; align-items: center; }}
    .dish-price {{ font-size: 1.2rem; font-weight: 800; color: #fb923c; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.5rem 1rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
    .cart-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 14px; padding: 1.5rem; height: fit-content; }}
    .cart-item {{ display: flex; justify-content: space-between; align-items: center; padding: 0.6rem 0; border-bottom: 1px solid var(--border); font-size: 0.9rem; }}
    .tracker {{ margin-top: 1.5rem; padding-top: 1rem; border-top: 1px solid var(--border); }}
    .step {{ display: flex; align-items: center; gap: 0.6rem; font-size: 0.85rem; color: var(--muted); margin-bottom: 0.5rem; }}
    .step.active {{ color: #fb923c; font-weight: 700; }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div class="badge">&#127828; GOURMET FOOD DELIVERY</div>
      <h1>{app_title}</h1>
      <p class="subtitle">{app_desc}</p>
    </div>

    <div class="layout">
      <div>
        <h3 style="margin-bottom: 1rem;">Chef's Featured Menu</h3>
        <div class="menu-grid">
          <div class="dish-card">
            <div>
              <div class="dish-title">Truffle Mushroom Burger</div>
              <p class="dish-desc">Angus beef patty with sautéed wild truffles, aged cheddar, and brioche bun.</p>
            </div>
            <div class="dish-footer">
              <span class="dish-price">$16.50</span>
              <button class="btn" onclick="addToCart('Truffle Burger', 16.50)">+ Add to Order</button>
            </div>
          </div>
          <div class="dish-card">
            <div>
              <div class="dish-title">Spicy Tuna Poke Bowl</div>
              <p class="dish-desc">Sashimi-grade tuna, avocado, edamame, and sriracha ponzu drizzle.</p>
            </div>
            <div class="dish-footer">
              <span class="dish-price">$18.00</span>
              <button class="btn" onclick="addToCart('Tuna Poke Bowl', 18.00)">+ Add to Order</button>
            </div>
          </div>
          <div class="dish-card">
            <div>
              <div class="dish-title">Artisan Margherita Pizza</div>
              <p class="dish-desc">San Marzano tomatoes, buffalo mozzarella, and fresh sweet basil.</p>
            </div>
            <div class="dish-footer">
              <span class="dish-price">$14.00</span>
              <button class="btn" onclick="addToCart('Margherita Pizza', 14.00)">+ Add to Order</button>
            </div>
          </div>
        </div>
      </div>

      <div class="cart-card">
        <h3 style="margin-bottom: 1rem;">Your Cart & Order</h3>
        <div id="cartItems">
          <div class="cart-item">
            <span>Truffle Burger x1</span>
            <b>$16.50</b>
          </div>
        </div>
        <div style="display: flex; justify-content: space-between; margin-top: 1rem; font-weight: 800; font-size: 1.1rem;">
          <span>Subtotal</span>
          <span id="cartTotal" style="color: #fb923c;">$16.50</span>
        </div>
        <button class="btn" style="width: 100%; margin-top: 1rem; padding: 0.75rem;" onclick="checkout()">Proceed to Checkout</button>

        <div class="tracker">
          <h4 style="font-size: 0.9rem; margin-bottom: 0.75rem;">Live Order Tracking</h4>
          <div class="step active">&#9679; 1. Order Confirmed (18:05)</div>
          <div class="step active">&#9679; 2. Kitchen Preparing Meal</div>
          <div class="step">&#9675; 3. Courier Out for Delivery</div>
          <div class="step">&#9675; 4. Delivered to Doorstep</div>
        </div>
      </div>
    </div>
  </div>

  <script>
    let total = 16.50;
    function addToCart(name, price) {{
      total += price;
      const div = document.createElement('div');
      div.className = 'cart-item';
      div.innerHTML = `<span>${{name}} x1</span><b>$${{price.toFixed(2)}}</b>`;
      document.getElementById('cartItems').appendChild(div);
      document.getElementById('cartTotal').innerText = '$' + total.toFixed(2);
    }}
    function checkout() {{
      alert('Order Placed Successfully! Your delivery driver is assigned.');
    }}
  </script>
</body>
</html>"""

    # 4. LEARNING MANAGEMENT SYSTEM (LMS)
    if _has_kw("learning", "lms", "course", "curriculum", "lesson", "academy", "grading", "syllabus"):
        app_title = title if title and "SE IntelliPlatform" not in title else "EduSphere Learning Management System"
        app_desc = desc if desc else "Interactive Online Courses, Lesson Modules & Student Academic Mastery"
        return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #090e17; --card-bg: rgba(15, 23, 42, 0.85); --border: rgba(255, 255, 255, 0.08);
      --accent: #10b981; --accent-hover: #059669; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #06281e 0%, #090e17 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-start; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(16, 185, 129, 0.15); color: #34d399; border: 1px solid rgba(16, 185, 129, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #6ee7b7 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
    .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
    .stat-title {{ font-size: 0.8rem; text-transform: uppercase; color: var(--muted); font-weight: 700; }}
    .stat-val {{ font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 0.4rem; color: #fff; }}
    .main-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; }}
    .course-item {{ display: flex; justify-content: space-between; align-items: center; padding: 1.25rem 0; border-bottom: 1px solid var(--border); flex-wrap: wrap; gap: 1rem; }}
    .course-meta h4 {{ font-size: 1.1rem; font-weight: 700; }}
    .course-meta p {{ color: var(--muted); font-size: 0.85rem; }}
    .progress-bar {{ width: 180px; height: 8px; background: rgba(255,255,255,0.1); border-radius: 4px; overflow: hidden; margin-top: 0.5rem; }}
    .progress-fill {{ height: 100%; background: var(--accent); border-radius: 4px; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="badge">&#127891; LEARNING MANAGEMENT SYSTEM</div>
        <h1>{app_title}</h1>
        <p class="subtitle">{app_desc}</p>
      </div>
      <div>
        <button class="btn" onclick="alert('Enrolled in new specialization!')">+ Enroll Course</button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-title">Enrolled Courses</div>
        <div class="stat-val">5</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Modules Completed</div>
        <div class="stat-val">42 / 56</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Overall GPA</div>
        <div class="stat-val">3.92</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Study Streak</div>
        <div class="stat-val" style="color: #34d399;">14 Days</div>
      </div>
    </div>

    <div class="main-card">
      <h3 style="margin-bottom: 1rem;">Active Course Curriculum</h3>
      <div class="course-item">
        <div class="course-meta">
          <h4>CS-401: Advanced Distributed Systems Architecture</h4>
          <p>Prof. James Thorne &bull; 10 / 12 Lessons Completed</p>
          <div class="progress-bar"><div class="progress-fill" style="width: 83%;"></div></div>
        </div>
        <button class="btn" onclick="resumeLesson(this)">Resume Lesson</button>
      </div>
      <div class="course-item">
        <div class="course-meta">
          <h4>DS-202: Applied Machine Learning & Neural Networks</h4>
          <p>Dr. Lisa Rodriguez &bull; 6 / 8 Lessons Completed</p>
          <div class="progress-bar"><div class="progress-fill" style="width: 75%;"></div></div>
        </div>
        <button class="btn" onclick="resumeLesson(this)">Resume Lesson</button>
      </div>
    </div>
  </div>

  <script>
    function resumeLesson(btn) {{
      btn.innerText = 'In Progress...';
      setTimeout(() => alert('Launching interactive Jupyter notebook and lecture stream.'), 300);
    }}
  </script>
</body>
</html>"""

    # 5. UNIVERSAL GENERAL-PURPOSE DOMAIN SYNTHESIZER
    app_title = title if title and "SE IntelliPlatform" not in title else "Domain Application Platform"
    app_desc = desc if desc else "Custom application synthesized according to confirmed project specifications."
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{app_title} - Live Preview</title>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;700&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0b0f19; --card-bg: rgba(22, 30, 49, 0.85); --border: rgba(255, 255, 255, 0.1);
      --accent: #6366f1; --accent-hover: #4f46e5; --text: #f8fafc; --muted: #94a3b8;
    }}
    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: 'Plus Jakarta Sans', sans-serif;
      background: radial-gradient(circle at 50% 10%, #1e1b4b 0%, #0b0f19 75%);
      color: var(--text); min-height: 100vh; padding: 2rem;
    }}
    .container {{ max-width: 1200px; margin: 0 auto; }}
    .header {{ margin-bottom: 2rem; display: flex; justify-content: space-between; align-items: flex-start; }}
    .badge {{ display: inline-flex; align-items: center; gap: 0.4rem; background: rgba(99, 102, 241, 0.15); color: #818cf8; border: 1px solid rgba(99, 102, 241, 0.3); padding: 0.3rem 0.8rem; border-radius: 9999px; font-size: 0.8rem; font-weight: 700; margin-bottom: 0.5rem; }}
    h1 {{ font-size: 2.2rem; font-weight: 800; background: linear-gradient(135deg, #fff 30%, #a5b4fc 100%); -webkit-background-clip: text; -webkit-text-fill-color: transparent; }}
    .subtitle {{ color: var(--muted); font-size: 0.95rem; margin-top: 0.25rem; }}
    .stats-grid {{ display: grid; grid-template-columns: repeat(auto-fit, minmax(240px, 1fr)); gap: 1.25rem; margin-bottom: 2rem; }}
    .stat-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 12px; padding: 1.25rem; }}
    .stat-title {{ font-size: 0.8rem; text-transform: uppercase; color: var(--muted); font-weight: 700; }}
    .stat-val {{ font-size: 1.8rem; font-weight: 800; font-family: 'JetBrains Mono', monospace; margin-top: 0.4rem; color: #fff; }}
    .main-card {{ background: var(--card-bg); border: 1px solid var(--border); border-radius: 16px; padding: 1.5rem; }}
    .btn {{ background: var(--accent); color: #fff; border: none; padding: 0.6rem 1.2rem; border-radius: 8px; font-weight: 600; cursor: pointer; transition: background 0.2s; }}
    .btn:hover {{ background: var(--accent-hover); }}
    .btn-secondary {{ background: rgba(255, 255, 255, 0.08); color: var(--text); border: 1px solid var(--border); margin-left: 0.5rem; }}
    table {{ width: 100%; border-collapse: collapse; text-align: left; font-size: 0.9rem; margin-top: 1rem; }}
    th {{ padding: 0.75rem 1rem; color: var(--muted); font-size: 0.8rem; text-transform: uppercase; border-bottom: 1px solid var(--border); }}
    td {{ padding: 1rem; border-bottom: 1px solid var(--border); }}
  </style>
</head>
<body>
  <div class="container">
    <div class="header">
      <div>
        <div class="badge">&#9881; DOMAIN APPLICATION PLATFORM</div>
        <h1>{app_title}</h1>
        <p class="subtitle">{app_desc}</p>
      </div>
      <div>
        <button class="btn" onclick="addRecord()">+ Add Record</button>
        <button class="btn btn-secondary" onclick="exportData()">Export CSV</button>
      </div>
    </div>

    <div class="stats-grid">
      <div class="stat-card">
        <div class="stat-title">Managed Records</div>
        <div class="stat-val" id="recordCount">48</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Active Services</div>
        <div class="stat-val">99.9%</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Domain Throughput</div>
        <div class="stat-val">1.2k ops/s</div>
      </div>
      <div class="stat-card">
        <div class="stat-title">Efficiency Index</div>
        <div class="stat-val" style="color: #34d399;">Optimal</div>
      </div>
    </div>

    <div class="main-card">
      <h3 style="margin-bottom: 1rem;">Domain Resources & Entity Explorer</h3>
      <table id="domainTable">
        <thead>
          <tr>
            <th>ID</th>
            <th>Resource Identifier</th>
            <th>Status</th>
            <th>Last Updated</th>
            <th>Actions</th>
          </tr>
        </thead>
        <tbody id="domainBody">
          <tr>
            <td><code>RES-01</code></td>
            <td><b>Primary Resource Cluster</b></td>
            <td><span style="color: #34d399; font-weight: 700;">Active</span></td>
            <td>Just now</td>
            <td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="this.closest('tr').remove()">Remove</button></td>
          </tr>
        </tbody>
      </table>
    </div>
  </div>

  <script>
    function addRecord() {{
      const id = 'RES-0' + (document.querySelectorAll('#domainBody tr').length + 1);
      const name = prompt('Enter resource name:') || 'Secondary Service Node';
      const tr = document.createElement('tr');
      tr.innerHTML = `<td><code>${{id}}</code></td><td><b>${{name}}</b></td><td><span style="color: #34d399; font-weight: 700;">Active</span></td><td>Just now</td><td><button class="btn btn-secondary" style="padding: 0.3rem 0.6rem; font-size: 0.8rem;" onclick="this.closest('tr').remove()">Remove</button></td>`;
      document.getElementById('domainBody').appendChild(tr);
      document.getElementById('recordCount').innerText = document.querySelectorAll('#domainBody tr').length;
    }}
    function exportData() {{
      alert('Exported domain configuration CSV.');
    }}
  </script>
</body>
</html>"""
