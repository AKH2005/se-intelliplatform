import React, { useState } from 'react';
import LoginPage, { UserProfile } from './components/LoginPage';

export default function App() {
  const [isLoginOpen, setIsLoginOpen] = useState(false);
  const [currentUser, setCurrentUser] = useState<UserProfile | null>(null);
  const [timeRange, setTimeRange] = useState('30D');
  const [metricsSearch, setMetricsSearch] = useState('');

  const handleExportCSV = () => {
    const rows = [
      ['Metric', 'Category', 'Value', 'Target', 'Change', 'Status'],
      ['Total ARR / Revenue', 'Financial', '$1,428,500', '$1,350,000', '+14.8%', 'Exceeded'],
      ['Monthly Active Workspaces', 'Product', '3,842', '3,500', '+21.4%', 'Exceeded'],
      ['Trial-to-Paid Conversion', 'Product', '24.6%', '25.0%', '-0.4%', 'On Track'],
      ['Net Revenue Retention (NRR)', 'Retention', '122.4%', '118.0%', '+4.4%', 'Exceeded'],
      ['Customer Gross Churn Rate', 'Retention', '1.8%', '< 2.5%', '-0.4%', 'On Track']
    ];
    const csvContent = rows.map(r => r.map(c => `"${c.replace(/"/g, '""')}"`).join(',')).join('\n');
    const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
    const url = URL.createObjectURL(blob);
    const link = document.createElement('a');
    link.setAttribute('href', url);
    link.setAttribute('download', 'executive-analytics-metrics.csv');
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  };

  return (
    <div className="container" style={{ maxWidth: '1380px', margin: '0 auto', padding: '1.5rem', fontFamily: 'sans-serif' }}>
      <header className="header" style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1.5rem', borderBottom: '1px solid rgba(255,255,255,0.1)', paddingBottom: '1rem' }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: '1rem' }}>
          <div style={{ width: '40px', height: '40px', borderRadius: '10px', background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', display: 'flex', alignItems: 'center', justifyContent: 'center', color: '#fff', fontWeight: 800 }}>EA</div>
          <div>
            <h1 style={{ margin: 0, fontSize: '1.4rem', color: '#fff' }}>Executive Analytics Dashboard</h1>
            <span style={{ fontSize: '0.75rem', color: '#10b981', fontWeight: 700 }}>● LIVE STREAM</span>
          </div>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '0.75rem' }}>
          <div style={{ display: 'inline-flex', background: '#111726', borderRadius: '8px', padding: '2px', border: '1px solid rgba(255,255,255,0.1)' }}>
            {['7D', '30D', '90D', '1Y'].map(t => (
              <button
                key={t}
                onClick={() => setTimeRange(t)}
                style={{
                  background: timeRange === t ? '#6366f1' : 'transparent',
                  color: timeRange === t ? '#fff' : '#94a3b8',
                  border: 'none',
                  padding: '0.3rem 0.6rem',
                  borderRadius: '6px',
                  cursor: 'pointer',
                  fontWeight: 600,
                  fontSize: '0.75rem'
                }}
              >
                {t}
              </button>
            ))}
          </div>

          <button id="btn-export-csv" onClick={handleExportCSV} style={{ background: '#1e293b', border: '1px solid rgba(255,255,255,0.1)', color: '#fff', padding: '0.45rem 0.85rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 600, fontSize: '0.8rem' }}>
            Export CSV
          </button>

          {currentUser ? (
            <div style={{ display: 'inline-flex', alignItems: 'center', gap: '0.5rem', background: 'rgba(99,102,241,0.15)', padding: '0.35rem 0.75rem', borderRadius: '8px', border: '1px solid rgba(99,102,241,0.3)', color: '#fff' }}>
              <span>👤</span>
              <span style={{ fontWeight: 700, fontSize: '0.85rem' }}>{currentUser.name}</span>
              <button id="btn-logout" onClick={() => setCurrentUser(null)} style={{ background: 'transparent', border: 'none', color: '#ef4444', cursor: 'pointer', fontSize: '0.75rem', marginLeft: '0.5rem' }}>Log Out</button>
            </div>
          ) : (
            <button
              id="btn-open-login"
              onClick={() => setIsLoginOpen(true)}
              style={{ background: 'linear-gradient(135deg, #6366f1, #8b5cf6)', border: 'none', color: '#fff', padding: '0.45rem 0.95rem', borderRadius: '8px', cursor: 'pointer', fontWeight: 700, fontSize: '0.8rem' }}
            >
              🔑 Sign In / Login
            </button>
          )}
        </div>
      </header>

      {/* 4 KPI Cards */}
      <section style={{ display: 'grid', gridTemplateColumns: 'repeat(4, 1fr)', gap: '1rem', marginBottom: '1.5rem' }}>
        <div style={{ background: '#111726', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem' }}><span>Total ARR / Revenue</span><span style={{ color: '#10b981', fontWeight: 700 }}>+14.8%</span></div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', marginTop: '0.3rem' }}>$1,428,500</div>
        </div>
        <div style={{ background: '#111726', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem' }}><span>Active Workspaces</span><span style={{ color: '#10b981', fontWeight: 700 }}>+21.4%</span></div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', marginTop: '0.3rem' }}>3,842</div>
        </div>
        <div style={{ background: '#111726', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem' }}><span>Conversion Rate</span><span style={{ color: '#10b981', fontWeight: 700 }}>+3.2%</span></div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', marginTop: '0.3rem' }}>24.6%</div>
        </div>
        <div style={{ background: '#111726', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
          <div style={{ display: 'flex', justifyContent: 'space-between', color: '#94a3b8', fontSize: '0.8rem' }}><span>Customer Retention</span><span style={{ color: '#10b981', fontWeight: 700 }}>+4.4%</span></div>
          <div style={{ fontSize: '1.6rem', fontWeight: 800, color: '#fff', marginTop: '0.3rem' }}>98.2%</div>
        </div>
      </section>

      {/* Filterable Metrics Table */}
      <section style={{ background: '#111726', padding: '1.25rem', borderRadius: '12px', border: '1px solid rgba(255,255,255,0.08)' }}>
        <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center', marginBottom: '1rem' }}>
          <h3 style={{ margin: 0, color: '#fff', fontSize: '1rem' }}>Key Performance Metrics</h3>
          <input
            id="metricsSearch"
            type="text"
            placeholder="Search metrics..."
            value={metricsSearch}
            onChange={e => setMetricsSearch(e.target.value)}
            style={{ background: '#0a0d14', border: '1px solid rgba(255,255,255,0.1)', borderRadius: '8px', padding: '0.4rem 0.8rem', color: '#fff', fontSize: '0.8rem' }}
          />
        </div>
        <table style={{ width: '100%', borderCollapse: 'collapse', color: '#fff', fontSize: '0.85rem' }}>
          <thead>
            <tr style={{ textAlign: 'left', borderBottom: '1px solid rgba(255,255,255,0.1)', color: '#94a3b8' }}>
              <th style={{ padding: '0.6rem' }}>Metric</th>
              <th style={{ padding: '0.6rem' }}>Category</th>
              <th style={{ padding: '0.6rem' }}>Current</th>
              <th style={{ padding: '0.6rem' }}>Target</th>
              <th style={{ padding: '0.6rem' }}>Change</th>
              <th style={{ padding: '0.6rem' }}>Status</th>
            </tr>
          </thead>
          <tbody>
            {[
              { name: 'Total ARR / Revenue', cat: 'Financial', val: '$1,428,500', target: '$1,350,000', change: '+14.8%', status: 'Exceeded' },
              { name: 'Monthly Active Workspaces', cat: 'Product', val: '3,842', target: '3,500', change: '+21.4%', status: 'Exceeded' },
              { name: 'Trial-to-Paid Conversion', cat: 'Product', val: '24.6%', target: '25.0%', change: '-0.4%', status: 'On Track' },
              { name: 'Net Revenue Retention (NRR)', cat: 'Retention', val: '122.4%', target: '118.0%', change: '+4.4%', status: 'Exceeded' },
              { name: 'Customer Gross Churn Rate', cat: 'Retention', val: '1.8%', target: '< 2.5%', change: '-0.4%', status: 'On Track' },
            ]
              .filter(m => !metricsSearch || m.name.toLowerCase().includes(metricsSearch.toLowerCase()))
              .map((m, idx) => (
                <tr key={idx} style={{ borderBottom: '1px solid rgba(255,255,255,0.05)' }}>
                  <td style={{ padding: '0.6rem', fontWeight: 600 }}>{m.name}</td>
                  <td style={{ padding: '0.6rem', color: '#94a3b8' }}>{m.cat}</td>
                  <td style={{ padding: '0.6rem', fontWeight: 700 }}>{m.val}</td>
                  <td style={{ padding: '0.6rem', color: '#94a3b8' }}>{m.target}</td>
                  <td style={{ padding: '0.6rem', color: m.change.startsWith('+') ? '#10b981' : '#f59e0b', fontWeight: 700 }}>{m.change}</td>
                  <td style={{ padding: '0.6rem' }}><span style={{ background: 'rgba(16,185,129,0.15)', color: '#10b981', padding: '0.2rem 0.5rem', borderRadius: '9999px', fontSize: '0.75rem', fontWeight: 700 }}>{m.status}</span></td>
                </tr>
              ))}
          </tbody>
        </table>
      </section>

      <LoginPage
        isOpen={isLoginOpen}
        onClose={() => setIsLoginOpen(false)}
        onLoginSuccess={(u) => {
          setCurrentUser(u);
          setIsLoginOpen(false);
        }}
      />
    </div>
  );
}
