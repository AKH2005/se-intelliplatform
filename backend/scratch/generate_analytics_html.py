# Test and verify Executive Analytics Dashboard HTML generator

def get_analytics_dashboard_html(title: str = "Executive Analytics Dashboard", desc: str = "", project_id: str = None) -> str:
    # Safe title and desc
    clean_title = title or "Executive Analytics Dashboard"
    clean_desc = desc or "Executive analytics dashboard with revenue charts, user retention metrics, conversion funnel, and team performance KPIs"
    
    return f"""<!DOCTYPE html>
<html lang="en">
<head>
  <meta charset="UTF-8" />
  <meta name="viewport" content="width=device-width, initial-scale=1.0" />
  <title>{clean_title} - Executive Analytics Portal</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700;800&family=JetBrains+Mono:wght@400;600&display=swap" rel="stylesheet">
  <style>
    :root {{
      --bg: #0a0d14;
      --surface: #111726;
      --surface-card: rgba(17, 24, 39, 0.75);
      --surface-hover: #1e293b;
      --border: rgba(255, 255, 255, 0.08);
      --border-accent: rgba(99, 102, 241, 0.3);
      --text: #f8fafc;
      --text-muted: #94a3b8;
      --accent-primary: #6366f1;
      --accent-violet: #8b5cf6;
      --accent-cyan: #06b6d4;
      --success: #10b981;
      --success-bg: rgba(16, 185, 129, 0.15);
      --warning: #f59e0b;
      --warning-bg: rgba(245, 158, 11, 0.15);
      --danger: #ef4444;
      --danger-bg: rgba(239, 68, 68, 0.15);
      --font-sans: 'Plus Jakarta Sans', system-ui, -apple-system, sans-serif;
      --font-mono: 'JetBrains Mono', monospace;
    }}

    body.light-theme {{
      --bg: #f8fafc;
      --surface: #ffffff;
      --surface-card: #ffffff;
      --surface-hover: #f1f5f9;
      --border: #e2e8f0;
      --border-accent: rgba(99, 102, 241, 0.4);
      --text: #0f172a;
      --text-muted: #64748b;
    }}

    * {{ box-sizing: border-box; margin: 0; padding: 0; }}
    body {{
      font-family: var(--font-sans);
      background-color: var(--bg);
      color: var(--text);
      min-height: 100vh;
      padding: 1.5rem;
      transition: background 0.2s ease, color 0.2s ease;
      line-height: 1.5;
    }}

    .container {{
      max-width: 1380px;
      margin: 0 auto;
      display: flex;
      flex-direction: column;
      gap: 1.75rem;
    }}

    /* Top Navigation Header */
    .header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      flex-wrap: wrap;
      gap: 1rem;
      padding-bottom: 1.25rem;
      border-bottom: 1px solid var(--border);
    }}

    .header-left {{
      display: flex;
      align-items: center;
      gap: 1rem;
    }}

    .app-icon {{
      width: 44px;
      height: 44px;
      border-radius: 12px;
      background: linear-gradient(135deg, #6366f1, #8b5cf6);
      display: flex;
      align-items: center;
      justify-content: center;
      color: #fff;
      font-weight: 800;
      font-size: 1.2rem;
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.35);
    }}

    .app-title-group h1 {{
      font-size: 1.45rem;
      font-weight: 700;
      letter-spacing: -0.02em;
      display: flex;
      align-items: center;
      gap: 0.6rem;
    }}

    .live-badge {{
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      font-size: 0.7rem;
      font-weight: 700;
      color: var(--success);
      background: var(--success-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
      padding: 0.2rem 0.55rem;
      border-radius: 9999px;
      text-transform: uppercase;
      letter-spacing: 0.05em;
    }}

    .live-dot {{
      width: 6px;
      height: 6px;
      border-radius: 50%;
      background: var(--success);
      box-shadow: 0 0 8px var(--success);
      animation: pulse-dot 2s infinite;
    }}

    @keyframes pulse-dot {{
      0% {{ transform: scale(0.95); opacity: 0.8; }}
      50% {{ transform: scale(1.2); opacity: 1; }}
      100% {{ transform: scale(0.95); opacity: 0.8; }}
    }}

    .app-subtitle {{
      font-size: 0.85rem;
      color: var(--text-muted);
      margin-top: 0.15rem;
    }}

    .header-actions {{
      display: flex;
      align-items: center;
      gap: 0.75rem;
      flex-wrap: wrap;
    }}

    /* Time range filter buttons */
    .filter-group {{
      display: inline-flex;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 3px;
      gap: 2px;
    }}

    .filter-btn {{
      background: transparent;
      border: none;
      color: var(--text-muted);
      padding: 0.35rem 0.7rem;
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .filter-btn:hover {{
      color: var(--text);
    }}

    .filter-btn.active {{
      background: var(--accent-primary);
      color: #ffffff;
      box-shadow: 0 2px 6px rgba(99, 102, 241, 0.35);
    }}

    .btn {{
      display: inline-flex;
      align-items: center;
      gap: 0.45rem;
      padding: 0.45rem 0.85rem;
      font-size: 0.82rem;
      font-weight: 600;
      border-radius: 8px;
      cursor: pointer;
      border: 1px solid var(--border);
      background: var(--surface);
      color: var(--text);
      transition: all 0.15s ease;
      text-decoration: none;
    }}

    .btn:hover {{
      background: var(--surface-hover);
      border-color: rgba(255, 255, 255, 0.2);
    }}

    .btn-primary {{
      background: linear-gradient(135deg, var(--accent-primary), var(--accent-violet));
      color: #ffffff;
      border: 1px solid rgba(255, 255, 255, 0.15);
      box-shadow: 0 2px 10px rgba(99, 102, 241, 0.3);
    }}

    .btn-primary:hover {{
      box-shadow: 0 4px 14px rgba(99, 102, 241, 0.45);
      transform: translateY(-1px);
    }}

    /* KPI Summary Cards Grid */
    .kpi-grid {{
      display: grid;
      grid-template-columns: repeat(4, 1fr);
      gap: 1.25rem;
    }}

    .kpi-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.35rem;
      backdrop-filter: blur(12px);
      transition: transform 0.2s ease, border-color 0.2s ease, box-shadow 0.2s ease;
      position: relative;
      overflow: hidden;
    }}

    .kpi-card:hover {{
      transform: translateY(-2px);
      border-color: var(--border-accent);
      box-shadow: 0 8px 24px rgba(0, 0, 0, 0.3);
    }}

    .kpi-card::before {{
      content: '';
      position: absolute;
      top: 0;
      left: 0;
      right: 0;
      height: 3px;
      background: linear-gradient(90deg, var(--accent-primary), var(--accent-cyan));
      opacity: 0.7;
    }}

    .kpi-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 0.75rem;
    }}

    .kpi-label {{
      font-size: 0.82rem;
      font-weight: 600;
      color: var(--text-muted);
      text-transform: uppercase;
      letter-spacing: 0.04em;
    }}

    .kpi-trend {{
      display: inline-flex;
      align-items: center;
      gap: 0.25rem;
      font-size: 0.75rem;
      font-weight: 700;
      padding: 0.15rem 0.45rem;
      border-radius: 6px;
    }}

    .trend-up {{
      color: var(--success);
      background: var(--success-bg);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .trend-down {{
      color: var(--danger);
      background: var(--danger-bg);
      border: 1px solid rgba(239, 68, 68, 0.3);
    }}

    .kpi-value {{
      font-size: 2.1rem;
      font-weight: 800;
      letter-spacing: -0.03em;
      color: var(--text);
      font-family: var(--font-sans);
    }}

    .kpi-subtext {{
      font-size: 0.75rem;
      color: var(--text-muted);
      margin-top: 0.45rem;
    }}

    /* Charts Section */
    .charts-grid {{
      display: grid;
      grid-template-columns: 2fr 1fr;
      gap: 1.25rem;
    }}

    .chart-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.35rem;
      backdrop-filter: blur(12px);
      display: flex;
      flex-direction: column;
    }}

    .chart-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
    }}

    .chart-title {{
      font-size: 1.05rem;
      font-weight: 700;
      letter-spacing: -0.01em;
    }}

    .chart-subtitle {{
      font-size: 0.78rem;
      color: var(--text-muted);
      margin-top: 0.1rem;
    }}

    /* SVG Chart */
    .svg-chart-container {{
      width: 100%;
      height: 240px;
      position: relative;
    }}

    svg.trend-chart {{
      width: 100%;
      height: 100%;
      overflow: visible;
    }}

    .chart-point {{
      cursor: pointer;
      transition: r 0.15s ease, fill 0.15s ease;
    }}

    .chart-point:hover {{
      r: 6;
      fill: #ffffff;
      stroke: var(--accent-primary);
      stroke-width: 3;
    }}

    /* Funnel Bars */
    .funnel-list {{
      display: flex;
      flex-direction: column;
      gap: 1rem;
      margin-top: 0.5rem;
    }}

    .funnel-item {{
      display: flex;
      flex-direction: column;
      gap: 0.35rem;
    }}

    .funnel-info {{
      display: flex;
      justify-content: space-between;
      font-size: 0.82rem;
    }}

    .funnel-label {{
      font-weight: 600;
      color: var(--text);
    }}

    .funnel-stats {{
      color: var(--text-muted);
      font-family: var(--font-mono);
      font-size: 0.78rem;
    }}

    .funnel-bar-track {{
      height: 10px;
      background: rgba(255, 255, 255, 0.06);
      border-radius: 9999px;
      overflow: hidden;
      position: relative;
    }}

    .funnel-bar-fill {{
      height: 100%;
      border-radius: 9999px;
      background: linear-gradient(90deg, var(--accent-primary), var(--accent-cyan));
      transition: width 0.6s cubic-bezier(0.16, 1, 0.3, 1);
    }}

    /* Table Section */
    .table-card {{
      background: var(--surface-card);
      border: 1px solid var(--border);
      border-radius: 14px;
      padding: 1.35rem;
      backdrop-filter: blur(12px);
    }}

    .table-toolbar {{
      display: flex;
      justify-content: space-between;
      align-items: center;
      margin-bottom: 1.25rem;
      flex-wrap: wrap;
      gap: 1rem;
    }}

    .search-box {{
      position: relative;
      min-width: 280px;
    }}

    .search-input {{
      width: 100%;
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.5rem 0.85rem 0.5rem 2.2rem;
      font-size: 0.82rem;
      color: var(--text);
      outline: none;
      transition: border-color 0.15s ease;
    }}

    .search-input:focus {{
      border-color: var(--accent-primary);
    }}

    .search-icon {{
      position: absolute;
      left: 0.75rem;
      top: 50%;
      transform: translateY(-50%);
      color: var(--text-muted);
      pointer-events: none;
    }}

    .category-tabs {{
      display: flex;
      gap: 0.5rem;
    }}

    .tab-btn {{
      background: transparent;
      border: 1px solid transparent;
      color: var(--text-muted);
      padding: 0.35rem 0.75rem;
      font-size: 0.78rem;
      font-weight: 600;
      border-radius: 6px;
      cursor: pointer;
      transition: all 0.15s ease;
    }}

    .tab-btn.active {{
      background: rgba(99, 102, 241, 0.15);
      color: #818cf8;
      border-color: rgba(99, 102, 241, 0.3);
    }}

    .data-table {{
      width: 100%;
      border-collapse: collapse;
      text-align: left;
      font-size: 0.82rem;
    }}

    .data-table th {{
      background: rgba(255, 255, 255, 0.02);
      color: var(--text-muted);
      padding: 0.75rem 1rem;
      font-weight: 600;
      border-bottom: 1px solid var(--border);
      cursor: pointer;
      user-select: none;
    }}

    .data-table th:hover {{
      color: var(--text);
    }}

    .data-table td {{
      padding: 0.85rem 1rem;
      border-bottom: 1px solid var(--border);
      color: var(--text);
    }}

    .data-table tr:hover td {{
      background: rgba(255, 255, 255, 0.02);
    }}

    .status-pill {{
      display: inline-block;
      padding: 0.2rem 0.5rem;
      border-radius: 9999px;
      font-size: 0.72rem;
      font-weight: 700;
      text-transform: uppercase;
      letter-spacing: 0.03em;
    }}

    .status-exceeded {{
      background: var(--success-bg);
      color: var(--success);
      border: 1px solid rgba(16, 185, 129, 0.3);
    }}

    .status-ontrack {{
      background: rgba(6, 182, 212, 0.15);
      color: #22d3ee;
      border: 1px solid rgba(6, 182, 212, 0.3);
    }}

    .status-atrisk {{
      background: var(--warning-bg);
      color: var(--warning);
      border: 1px solid rgba(245, 158, 11, 0.3);
    }}

    /* Modal */
    .modal-backdrop {{
      display: none;
      position: fixed;
      top: 0;
      left: 0;
      right: 0;
      bottom: 0;
      background: rgba(0, 0, 0, 0.75);
      backdrop-filter: blur(6px);
      z-index: 1000;
      align-items: center;
      justify-content: center;
    }}

    .modal-backdrop.open {{
      display: flex;
    }}

    .modal-content {{
      background: var(--surface);
      border: 1px solid var(--border);
      border-radius: 16px;
      width: 100%;
      max-width: 480px;
      padding: 1.75rem;
      box-shadow: 0 20px 50px rgba(0, 0, 0, 0.6);
      display: flex;
      flex-direction: column;
      gap: 1.25rem;
    }}

    .modal-header {{
      display: flex;
      justify-content: space-between;
      align-items: center;
    }}

    .modal-title {{
      font-size: 1.15rem;
      font-weight: 700;
    }}

    .form-group {{
      display: flex;
      flex-direction: column;
      gap: 0.4rem;
    }}

    .form-label {{
      font-size: 0.78rem;
      font-weight: 600;
      color: var(--text-muted);
    }}

    .form-input {{
      background: rgba(0, 0, 0, 0.2);
      border: 1px solid var(--border);
      border-radius: 8px;
      padding: 0.55rem 0.85rem;
      font-size: 0.85rem;
      color: var(--text);
      outline: none;
    }}

    .form-input:focus {{
      border-color: var(--accent-primary);
    }}

    .modal-actions {{
      display: flex;
      justify-content: flex-end;
      gap: 0.75rem;
      margin-top: 0.5rem;
    }}

    /* Responsive Queries */
    @media (max-width: 1024px) {{
      .kpi-grid {{
        grid-template-columns: repeat(2, 1fr);
      }}
      .charts-grid {{
        grid-template-columns: 1fr;
      }}
    }}

    @media (max-width: 640px) {{
      body {{
        padding: 1rem;
      }}
      .kpi-grid {{
        grid-template-columns: 1fr;
      }}
      .header {{
        flex-direction: column;
        align-items: flex-start;
      }}
      .table-toolbar {{
        flex-direction: column;
        align-items: stretch;
      }}
      .search-box {{
        min-width: 100%;
      }}
    }}
  </style>
</head>
<body>
  <div class="container">
    <!-- Top Header -->
    <header class="header">
      <div class="header-left">
        <div class="app-icon">EA</div>
        <div class="app-title-group">
          <h1>
            <span>{clean_title}</span>
            <span class="live-badge"><span class="live-dot"></span> LIVE STREAM</span>
          </h1>
          <p class="app-subtitle">{clean_desc}</p>
        </div>
      </div>

      <div class="header-actions">
        <!-- Time Range Selector -->
        <div class="filter-group" role="group" aria-label="Time range filters">
          <button type="button" class="filter-btn" onclick="setTimeRange('7D')">7D</button>
          <button type="button" class="filter-btn active" onclick="setTimeRange('30D')">30D</button>
          <button type="button" class="filter-btn" onclick="setTimeRange('90D')">90D</button>
          <button type="button" class="filter-btn" onclick="setTimeRange('1Y')">1Y</button>
        </div>

        <button type="button" class="btn" onclick="toggleTheme()" title="Toggle Dark/Light Mode">
          <span id="themeIcon">☀️</span>
        </button>

        <button type="button" class="btn btn-primary" onclick="openAddMetricModal()">
          <span>+ Add Metric</span>
        </button>

        <button type="button" class="btn" onclick="exportCSV()">
          <span>Export CSV</span>
        </button>
      </div>
    </header>

    <!-- 4 KPI Cards Grid -->
    <section class="kpi-grid" aria-label="Key Performance Indicators">
      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Total ARR / Revenue</span>
          <span class="kpi-trend trend-up">+14.8%</span>
        </div>
        <div class="kpi-value" id="kpiRevenue">$1,428,500</div>
        <div class="kpi-subtext">+12.4% vs previous 30-day cohort</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Active Workspaces</span>
          <span class="kpi-trend trend-up">+21.4%</span>
        </div>
        <div class="kpi-value" id="kpiWorkspaces">3,842</div>
        <div class="kpi-subtext">98.2% customer retention index</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Conversion Rate</span>
          <span class="kpi-trend trend-up">+3.2%</span>
        </div>
        <div class="kpi-value" id="kpiConversion">24.6%</div>
        <div class="kpi-subtext">Trial-to-paid funnel completion</div>
      </div>

      <div class="kpi-card">
        <div class="kpi-header">
          <span class="kpi-label">Customer Churn</span>
          <span class="kpi-trend trend-up">-0.4%</span>
        </div>
        <div class="kpi-value" id="kpiChurn">1.8%</div>
        <div class="kpi-subtext">Benchmark avg: 3.5% annually</div>
      </div>
    </section>

    <!-- Charts Grid -->
    <section class="charts-grid">
      <!-- Revenue Trajectory Chart -->
      <div class="chart-card">
        <div class="chart-header">
          <div>
            <h2 class="chart-title">Revenue & Growth Trajectory</h2>
            <p class="chart-subtitle">Monthly recurring revenue with continuous ARR forecast</p>
          </div>
          <span style="font-size: 0.75rem; color: #818cf8; font-weight: 700;">+28.5% YoY</span>
        </div>

        <div class="svg-chart-container">
          <svg class="trend-chart" viewBox="0 0 600 220" preserveAspectRatio="none">
            <defs>
              <linearGradient id="revenueGradient" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stop-color="#6366f1" stop-opacity="0.45"/>
                <stop offset="100%" stop-color="#6366f1" stop-opacity="0.0"/>
              </linearGradient>
            </defs>
            <!-- Grid Lines -->
            <line x1="40" y1="30" x2="580" y2="30" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4"/>
            <line x1="40" y1="80" x2="580" y2="80" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4"/>
            <line x1="40" y1="130" x2="580" y2="130" stroke="rgba(255,255,255,0.06)" stroke-dasharray="4"/>
            <line x1="40" y1="180" x2="580" y2="180" stroke="rgba(255,255,255,0.08)"/>

            <!-- Area fill -->
            <polygon points="50,180 50,150 110,135 170,142 230,118 290,105 350,92 410,74 470,62 530,42 570,30 570,180" fill="url(#revenueGradient)"/>

            <!-- Trend Line -->
            <polyline points="50,150 110,135 170,142 230,118 290,105 350,92 410,74 470,62 530,42 570,30" fill="none" stroke="#6366f1" stroke-width="3" stroke-linecap="round" stroke-linejoin="round"/>

            <!-- Hoverable points -->
            <circle class="chart-point" cx="50" cy="150" r="4" fill="#6366f1" data-date="Jan" data-val="$820k"/>
            <circle class="chart-point" cx="110" cy="135" r="4" fill="#6366f1" data-date="Feb" data-val="$890k"/>
            <circle class="chart-point" cx="170" cy="142" r="4" fill="#6366f1" data-date="Mar" data-val="$875k"/>
            <circle class="chart-point" cx="230" cy="118" r="4" fill="#6366f1" data-date="Apr" data-val="$990k"/>
            <circle class="chart-point" cx="290" cy="105" r="4" fill="#6366f1" data-date="May" data-val="$1.08M"/>
            <circle class="chart-point" cx="350" cy="92" r="4" fill="#6366f1" data-date="Jun" data-val="$1.16M"/>
            <circle class="chart-point" cx="410" cy="74" r="4" fill="#6366f1" data-date="Jul" data-val="$1.24M"/>
            <circle class="chart-point" cx="470" cy="62" r="4" fill="#6366f1" data-date="Aug" data-val="$1.31M"/>
            <circle class="chart-point" cx="530" cy="42" r="4" fill="#6366f1" data-date="Sep" data-val="$1.39M"/>
            <circle class="chart-point" cx="570" cy="30" r="4" fill="#6366f1" data-date="Oct" data-val="$1.42M"/>

            <!-- Axis Labels -->
            <text x="50" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Jan</text>
            <text x="170" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Mar</text>
            <text x="290" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">May</text>
            <text x="410" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Jul</text>
            <text x="530" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Sep</text>
            <text x="570" y="202" fill="var(--text-muted)" font-size="11" text-anchor="middle">Oct</text>
          </svg>
        </div>
      </div>

      <!-- Conversion Funnel Card -->
      <div class="chart-card">
        <div class="chart-header">
          <div>
            <h2 class="chart-title">Conversion Funnel</h2>
            <p class="chart-subtitle">End-to-end customer onboarding flow</p>
          </div>
          <span style="font-size: 0.75rem; color: #10b981; font-weight: 700;">Healthy</span>
        </div>

        <div class="funnel-list">
          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Total Visitors</span>
              <span class="funnel-stats">145,200 (100%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 100%;"></div>
            </div>
          </div>

          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Product Signups</span>
              <span class="funnel-stats">48,300 (33.3%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 33.3%;"></div>
            </div>
          </div>

          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Active Trials</span>
              <span class="funnel-stats">18,450 (12.7%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 12.7%;"></div>
            </div>
          </div>

          <div class="funnel-item">
            <div class="funnel-info">
              <span class="funnel-label">Enterprise Paid</span>
              <span class="funnel-stats">3,842 (2.6%)</span>
            </div>
            <div class="funnel-bar-track">
              <div class="funnel-bar-fill" style="width: 2.6%; background: #10b981;"></div>
            </div>
          </div>
        </div>
      </div>
    </section>

    <!-- Metrics Data Table -->
    <section class="table-card" aria-label="Performance Metrics">
      <div class="table-toolbar">
        <div>
          <h2 class="chart-title">Key Performance Indicators</h2>
          <p class="chart-subtitle">Detailed financial, operational, and retention benchmarks</p>
        </div>

        <div style="display: flex; gap: 0.75rem; flex-wrap: wrap;">
          <div class="search-box">
            <span class="search-icon">🔍</span>
            <input type="text" id="metricSearch" class="search-input" placeholder="Search metrics or dimensions..." onkeyup="filterTable()" />
          </div>

          <div class="category-tabs">
            <button type="button" class="tab-btn active" onclick="setCategoryFilter('all')">All</button>
            <button type="button" class="tab-btn" onclick="setCategoryFilter('Financial')">Financial</button>
            <button type="button" class="tab-btn" onclick="setCategoryFilter('Product')">Product</button>
            <button type="button" class="tab-btn" onclick="setCategoryFilter('Retention')">Retention</button>
          </div>
        </div>
      </div>

      <div style="overflow-x: auto;">
        <table class="data-table" id="metricsTable">
          <thead>
            <tr>
              <th onclick="sortTable(0)">Metric Name ↕</th>
              <th onclick="sortTable(1)">Category ↕</th>
              <th onclick="sortTable(2)">Current Value ↕</th>
              <th onclick="sortTable(3)">Target ↕</th>
              <th onclick="sortTable(4)">Trend ↕</th>
              <th>Status</th>
            </tr>
          </thead>
          <tbody id="metricsBody">
            <tr data-category="Financial">
              <td style="font-weight: 600;">Annual Recurring Revenue (ARR)</td>
              <td>Financial</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">$1,428,500</td>
              <td style="color: var(--text-muted);">$1,350,000</td>
              <td style="color: var(--success); font-weight: 700;">+14.8%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Financial">
              <td style="font-weight: 600;">Average Revenue Per User (ARPU)</td>
              <td>Financial</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">$371.80</td>
              <td style="color: var(--text-muted);">$350.00</td>
              <td style="color: var(--success); font-weight: 700;">+6.2%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Product">
              <td style="font-weight: 600;">Monthly Active Workspaces</td>
              <td>Product</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">3,842</td>
              <td style="color: var(--text-muted);">3,500</td>
              <td style="color: var(--success); font-weight: 700;">+21.4%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Product">
              <td style="font-weight: 600;">Trial-to-Paid Conversion</td>
              <td>Product</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">24.6%</td>
              <td style="color: var(--text-muted);">25.0%</td>
              <td style="color: var(--warning); font-weight: 700;">-0.4%</td>
              <td><span class="status-pill status-ontrack">On Track</span></td>
            </tr>
            <tr data-category="Retention">
              <td style="font-weight: 600;">Net Revenue Retention (NRR)</td>
              <td>Retention</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">122.4%</td>
              <td style="color: var(--text-muted);">118.0%</td>
              <td style="color: var(--success); font-weight: 700;">+4.4%</td>
              <td><span class="status-pill status-exceeded">Exceeded</span></td>
            </tr>
            <tr data-category="Retention">
              <td style="font-weight: 600;">Customer Gross Churn Rate</td>
              <td>Retention</td>
              <td style="font-family: var(--font-mono); font-weight: 700;">1.8%</td>
              <td style="color: var(--text-muted);">&lt; 2.5%</td>
              <td style="color: var(--success); font-weight: 700;">-0.4%</td>
              <td><span class="status-pill status-ontrack">On Track</span></td>
            </tr>
          </tbody>
        </table>
      </div>
    </section>
  </div>

  <!-- Add Metric Modal -->
  <div class="modal-backdrop" id="addMetricModal">
    <div class="modal-content">
      <div class="modal-header">
        <h3 class="modal-title">Add Custom KPI Metric</h3>
        <button type="button" class="btn" style="padding: 0.2rem 0.5rem;" onclick="closeAddMetricModal()">✕</button>
      </div>

      <div class="form-group">
        <label class="form-label" for="metricName">Metric Name</label>
        <input type="text" id="metricName" class="form-input" placeholder="e.g. Daily Active Users" />
      </div>

      <div class="form-group">
        <label class="form-label" for="metricCategory">Category</label>
        <select id="metricCategory" class="form-input">
          <option value="Financial">Financial</option>
          <option value="Product">Product</option>
          <option value="Retention">Retention</option>
        </select>
      </div>

      <div style="display: grid; grid-template-columns: 1fr 1fr; gap: 0.75rem;">
        <div class="form-group">
          <label class="form-label" for="metricVal">Current Value</label>
          <input type="text" id="metricVal" class="form-input" placeholder="e.g. 15,200" />
        </div>
        <div class="form-group">
          <label class="form-label" for="metricTarget">Target</label>
          <input type="text" id="metricTarget" class="form-input" placeholder="e.g. 12,000" />
        </div>
      </div>

      <div class="modal-actions">
        <button type="button" class="btn" onclick="closeAddMetricModal()">Cancel</button>
        <button type="button" class="btn btn-primary" onclick="submitNewMetric()">Save Metric</button>
      </div>
    </div>
  </div>

  <!-- Interactive JavaScript logic -->
  <script>
    // Theme toggle
    function toggleTheme() {{
      const isLight = document.body.classList.toggle('light-theme');
      document.getElementById('themeIcon').textContent = isLight ? '🌙' : '☀️';
    }}

    // Time range filter switching
    function setTimeRange(range) {{
      document.querySelectorAll('.filter-btn').forEach(btn => {{
        btn.classList.toggle('active', btn.textContent.trim() === range);
      }});

      const revElem = document.getElementById('kpiRevenue');
      const wsElem = document.getElementById('kpiWorkspaces');
      if (range === '7D') {{
        revElem.textContent = '$348,200';
        wsElem.textContent = '1,120';
      }} else if (range === '30D') {{
        revElem.textContent = '$1,428,500';
        wsElem.textContent = '3,842';
      }} else if (range === '90D') {{
        revElem.textContent = '$4,190,000';
        wsElem.textContent = '6,450';
      }} else if (range === '1Y') {{
        revElem.textContent = '$14,800,000';
        wsElem.textContent = '12,900';
      }}
    }}

    // Filter table by search query
    function filterTable() {{
      const query = (document.getElementById('metricSearch').value || '').toLowerCase();
      const rows = document.querySelectorAll('#metricsBody tr');
      rows.forEach(r => {{
        const text = r.textContent.toLowerCase();
        r.style.display = text.includes(query) ? '' : 'none';
      }});
    }}

    // Filter table by category tab
    function setCategoryFilter(cat) {{
      document.querySelectorAll('.tab-btn').forEach(b => {{
        b.classList.toggle('active', b.textContent.trim().toLowerCase() === cat.toLowerCase());
      }});

      const rows = document.querySelectorAll('#metricsBody tr');
      rows.forEach(r => {{
        if (cat === 'all' || r.getAttribute('data-category').toLowerCase() === cat.toLowerCase()) {{
          r.style.display = '';
        }} else {{
          r.style.display = 'none';
        }}
      }});
    }}

    // Sort table by column index
    let sortAsc = true;
    function sortTable(colIndex) {{
      const tbody = document.getElementById('metricsBody');
      const rows = Array.from(tbody.querySelectorAll('tr'));
      rows.sort((a, b) => {{
        const textA = a.children[colIndex].textContent.trim();
        const textB = b.children[colIndex].textContent.trim();
        return sortAsc ? textA.localeCompare(textB) : textB.localeCompare(textA);
      }});
      sortAsc = !sortAsc;
      rows.forEach(r => tbody.appendChild(r));
    }}

    // Modal controls
    function openAddMetricModal() {{
      document.getElementById('addMetricModal').classList.add('open');
    }}

    function closeAddMetricModal() {{
      document.getElementById('addMetricModal').classList.remove('open');
    }}

    function submitNewMetric() {{
      const name = document.getElementById('metricName').value.trim();
      const cat = document.getElementById('metricCategory').value;
      const val = document.getElementById('metricVal').value.trim() || '0';
      const target = document.getElementById('metricTarget').value.trim() || '0';

      if (!name) {{
        alert('Please enter a metric name');
        return;
      }}

      const tbody = document.getElementById('metricsBody');
      const tr = document.createElement('tr');
      tr.setAttribute('data-category', cat);
      tr.innerHTML = `
        <td style="font-weight: 600;">${{name}}</td>
        <td>${{cat}}</td>
        <td style="font-family: var(--font-mono); font-weight: 700;">${{val}}</td>
        <td style="color: var(--text-muted);">${{target}}</td>
        <td style="color: var(--success); font-weight: 700;">+5.0%</td>
        <td><span class="status-pill status-ontrack">On Track</span></td>
      `;
      tbody.prepend(tr);
      closeAddMetricModal();
      document.getElementById('metricName').value = '';
    }}

    // Export CSV
    function exportCSV() {{
      const rows = Array.from(document.querySelectorAll('#metricsTable tr'));
      const csv = rows.map(r => {{
        const cells = Array.from(r.querySelectorAll('th, td')).map(c => '"' + c.textContent.trim().replace(/"/g, '""') + '"');
        return cells.join(',');
      }}).join('\\n');

      const blob = new Blob([csv], {{ type: 'text/csv' }});
      const url = URL.createObjectURL(blob);
      const a = document.createElement('a');
      a.href = url;
      a.download = 'executive-analytics-metrics.csv';
      document.body.appendChild(a);
      a.click();
      document.body.removeChild(a);
    }}
  </script>
</body>
</html>"""

if __name__ == "__main__":
    html = get_analytics_dashboard_html()
    print("HTML length:", len(html))
    print("Contains ARR:", "$1,428,500" in html)
    print("Contains Funnel:", "Conversion Funnel" in html)
    print("Contains SVG:", "<svg" in html)

