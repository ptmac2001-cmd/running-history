import { useState, useEffect } from 'react';
import { NavLink } from 'react-router-dom';
import client from '../../api/client';

const links = [
  { to: '/', label: 'Dashboard', icon: '⬛' },
  { to: '/activities', label: 'Activities', icon: '🏃' },
  { to: '/analytics', label: 'Analytics', icon: '📊' },
  { to: '/heatmap', label: 'Heatmap', icon: '🗺️' },
];

export function Sidebar() {
  const [stravaConnected, setStravaConnected] = useState<boolean | null>(null);
  const [syncing, setSyncing] = useState(false);
  const [syncResult, setSyncResult] = useState<string | null>(null);

  useEffect(() => {
    client.get<{ connected: boolean }>('/auth/strava/status').then((r) => setStravaConnected(r.data.connected)).catch(() => setStravaConnected(false));
    if (new URLSearchParams(window.location.search).get('strava') === 'connected') {
      setStravaConnected(true);
      window.history.replaceState({}, '', window.location.pathname);
    }
  }, []);

  async function handleSync() {
    setSyncing(true);
    setSyncResult(null);
    try {
      const r = await client.post('/api/sync/strava');
      setSyncResult(`+${r.data.inserted} new`);
    } catch {
      setSyncResult('Sync failed');
    } finally {
      setSyncing(false);
    }
  }

  return (
    <nav style={{
      width: 200, minHeight: '100vh', background: '#1a1a2e',
      padding: '24px 0', display: 'flex', flexDirection: 'column', gap: 4,
    }}>
      <div style={{ color: '#e94560', fontWeight: 700, fontSize: 18, padding: '0 20px 20px' }}>
        Running History
      </div>
      {links.map(({ to, label, icon }) => (
        <NavLink
          key={to}
          to={to}
          end={to === '/'}
          style={({ isActive }) => ({
            display: 'block', padding: '10px 20px', textDecoration: 'none',
            color: isActive ? '#e94560' : '#ccc',
            background: isActive ? 'rgba(233,69,96,0.1)' : 'transparent',
            borderLeft: isActive ? '3px solid #e94560' : '3px solid transparent',
            fontSize: 14,
          })}
        >
          {icon} {label}
        </NavLink>
      ))}

      <div style={{ marginTop: 'auto', padding: '20px 20px 0', borderTop: '1px solid #333' }}>
        <div style={{ fontSize: 11, color: '#555', marginBottom: 8, textTransform: 'uppercase', letterSpacing: 1 }}>
          Strava
        </div>
        {stravaConnected === false && (
          <a
            href="http://localhost:8000/auth/strava"
            style={{
              display: 'block', padding: '8px 12px', background: '#fc4c02',
              color: '#fff', borderRadius: 4, fontSize: 12, textDecoration: 'none',
              textAlign: 'center',
            }}
          >
            Connect Strava
          </a>
        )}
        {stravaConnected === true && (
          <>
            <button
              onClick={handleSync}
              disabled={syncing}
              style={{
                width: '100%', padding: '8px 12px', background: syncing ? '#333' : '#fc4c02',
                color: '#fff', border: 'none', borderRadius: 4, fontSize: 12,
                cursor: syncing ? 'default' : 'pointer',
              }}
            >
              {syncing ? 'Syncing...' : 'Sync Now'}
            </button>
            {syncResult && (
              <div style={{ fontSize: 11, color: '#888', marginTop: 6, textAlign: 'center' }}>
                {syncResult}
              </div>
            )}
          </>
        )}
      </div>
    </nav>
  );
}
