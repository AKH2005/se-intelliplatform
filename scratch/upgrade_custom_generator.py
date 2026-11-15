"""
Upgrade custom application generation to support domain-specific application engines:
- Medical Application
- Music Player
- Food Delivery Application
- Learning Management System
- Universal Dynamic Domain Synthesizer
Uses word-boundary checks (_has_kw) so substrings like "tracking" do NOT match "track"!
"""

import ast
import re
from pathlib import Path

def generate_custom_html_engine():
    return '''def get_custom_interactive_html(title="Custom Application", desc="Domain-specific full-stack application synthesized according to confirmed project specifications."):
    import re
    combined = f"{title} {desc}".lower()

    def _has_kw(*words: str) -> bool:
        for w in words:
            if re.search(r'\\b' + re.escape(w.lower()) + r'\\b', combined):
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
      let csv = 'Patient ID,Name,Diagnosis,Physician,Severity\\n';
      document.querySelectorAll('#patientBody tr').forEach(row => {{
        const cols = Array.from(row.querySelectorAll('td')).map(td => td.innerText.trim());
        if (cols.length >= 5) csv += `${{cols[0]}},"${{cols[1]}}","${{cols[2]}}","${{cols[3]}}",${{cols[4]}}\\n`;
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
'''