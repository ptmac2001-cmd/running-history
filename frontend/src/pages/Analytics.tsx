import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line, PieChart, Pie, Cell, Legend } from 'recharts';
import { useByYear, useHRZones, usePaceTrend, usePersonalRecords, useStreak, useSources } from '../hooks/useAnalytics';
import { formatPace } from '../utils';

const ZONE_COLORS = ['#4caf50', '#8bc34a', '#ffc107', '#ff9800', '#f44336'];

export function Analytics() {
  const { data: byYear } = useByYear();
  const { data: paceTrend } = usePaceTrend();
  const { data: hrZones } = useHRZones();
  const { data: prs } = usePersonalRecords();
  const { data: streak } = useStreak();
  const { data: sources } = useSources();

  return (
    <div style={{ padding: 32, color: '#fff' }}>
      <h1 style={{ marginBottom: 32, fontSize: 24, fontWeight: 700 }}>Analytics</h1>

      {/* Streak */}
      {streak && (
        <div style={{ display: 'flex', gap: 16, marginBottom: 40 }}>
          <div style={{ background: '#16213e', borderRadius: 8, padding: '16px 24px' }}>
            <div style={{ color: '#888', fontSize: 12 }}>CURRENT STREAK</div>
            <div style={{ color: '#e94560', fontSize: 32, fontWeight: 700 }}>{streak.current_streak_days} days</div>
          </div>
          <div style={{ background: '#16213e', borderRadius: 8, padding: '16px 24px' }}>
            <div style={{ color: '#888', fontSize: 12 }}>LONGEST STREAK</div>
            <div style={{ color: '#fff', fontSize: 32, fontWeight: 700 }}>{streak.longest_streak_days} days</div>
            {streak.longest_streak_start && (
              <div style={{ color: '#666', fontSize: 12 }}>starting {streak.longest_streak_start}</div>
            )}
          </div>
        </div>
      )}

      {/* Personal Records */}
      {prs && prs.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <h2 style={{ fontSize: 16, marginBottom: 16, color: '#ccc' }}>Personal Records</h2>
          <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap' }}>
            {prs.map((pr) => (
              <div key={pr.distance_key} style={{
                background: '#16213e', borderRadius: 8, padding: '16px 24px', minWidth: 120,
                borderTop: '3px solid #e94560',
              }}>
                <div style={{ color: '#888', fontSize: 12 }}>{pr.label}</div>
                <div style={{ color: '#fff', fontSize: 22, fontWeight: 700 }}>{pr.formatted_time}</div>
                <div style={{ color: '#666', fontSize: 11 }}>{pr.set_at.slice(0, 10)}</div>
              </div>
            ))}
          </div>
        </div>
      )}

      {/* Yearly chart */}
      {byYear && byYear.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <h2 style={{ fontSize: 16, marginBottom: 16, color: '#ccc' }}>Distance by Year</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byYear}>
              <XAxis dataKey="year" stroke="#555" tick={{ fill: '#888', fontSize: 12 }} />
              <YAxis stroke="#555" tick={{ fill: '#888', fontSize: 12 }} unit=" mi" />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333', color: '#fff' }}
                formatter={(v: number | undefined, name: string | undefined) => {
                  if (v == null) return [v, name];
                  if (name === 'distance_miles') return [`${v.toFixed(0)} mi`, 'Distance'];
                  if (name === 'runs') return [v, 'Runs'];
                  return [v, name];
                }}
              />
              <Bar dataKey="distance_miles" fill="#e94560" radius={[2, 2, 0, 0]} name="distance_miles" />
              <Bar dataKey="runs" fill="#444" radius={[2, 2, 0, 0]} name="runs" />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Pace trend */}
      {paceTrend && paceTrend.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <h2 style={{ fontSize: 16, marginBottom: 16, color: '#ccc' }}>Pace Trend</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={paceTrend}>
              <XAxis dataKey="period" stroke="#555" tick={{ fill: '#888', fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis stroke="#555" tick={{ fill: '#888', fontSize: 12 }} reversed tickFormatter={formatPace} domain={['auto', 'auto']} />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333', color: '#fff' }}
                formatter={(v: number | undefined) => [v != null ? formatPace(v) : v, 'Avg Pace']}
              />
              <Line type="monotone" dataKey="avg_pace_sec_per_mile" stroke="#e94560" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}

      <div style={{ display: 'flex', gap: 32, flexWrap: 'wrap' }}>
        {/* HR Zones */}
        {hrZones && hrZones.some((z) => z.seconds > 0) && (
          <div style={{ flex: 1, minWidth: 280, marginBottom: 40 }}>
            <h2 style={{ fontSize: 16, marginBottom: 16, color: '#ccc' }}>HR Zones</h2>
            <ResponsiveContainer width="100%" height={200}>
              <PieChart>
                <Pie data={hrZones.filter((z) => z.seconds > 0)} dataKey="seconds" nameKey="label" cx="50%" cy="50%" outerRadius={80}>
                  {hrZones.map((_, i) => <Cell key={i} fill={ZONE_COLORS[i]} />)}
                </Pie>
                <Tooltip
                  contentStyle={{ background: '#1a1a2e', border: '1px solid #333', color: '#fff' }}
                  formatter={(_v: number | undefined, __: string | undefined, entry: any) => [`${entry.payload.percentage}%`, entry.payload.label]}
                />
                <Legend formatter={(value) => <span style={{ color: '#888', fontSize: 12 }}>{value}</span>} />
              </PieChart>
            </ResponsiveContainer>
          </div>
        )}

        {/* Sources */}
        {sources && sources.length > 0 && (
          <div style={{ flex: 1, minWidth: 280 }}>
            <h2 style={{ fontSize: 16, marginBottom: 16, color: '#ccc' }}>Data Sources</h2>
            <table style={{ width: '100%', fontSize: 13, borderCollapse: 'collapse' }}>
              <thead>
                <tr style={{ color: '#666', borderBottom: '1px solid #333' }}>
                  <th style={{ textAlign: 'left', padding: '6px 0' }}>Source</th>
                  <th style={{ textAlign: 'right', padding: '6px 0' }}>Runs</th>
                  <th style={{ textAlign: 'right', padding: '6px 0' }}>Earliest</th>
                  <th style={{ textAlign: 'right', padding: '6px 0' }}>Latest</th>
                </tr>
              </thead>
              <tbody>
                {sources.map((s) => (
                  <tr key={s.source} style={{ borderBottom: '1px solid #1e1e2e' }}>
                    <td style={{ padding: '8px 0', color: '#ccc' }}>{s.source}</td>
                    <td style={{ padding: '8px 0', color: '#ccc', textAlign: 'right' }}>{s.count}</td>
                    <td style={{ padding: '8px 0', color: '#666', textAlign: 'right' }}>{s.earliest ?? '—'}</td>
                    <td style={{ padding: '8px 0', color: '#666', textAlign: 'right' }}>{s.latest ?? '—'}</td>
                  </tr>
                ))}
              </tbody>
            </table>
          </div>
        )}
      </div>
    </div>
  );
}
