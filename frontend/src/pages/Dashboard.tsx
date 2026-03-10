import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, LineChart, Line } from 'recharts';
import { StatCard } from '../components/dashboard/StatCard';
import { SkeletonStatCards, SkeletonChart } from '../components/Skeleton';
import { useSummary, useByYear, usePaceTrend } from '../hooks/useAnalytics';
import { formatPace } from '../utils';

export function Dashboard() {
  const { data: summary, isLoading } = useSummary();
  const { data: byYear } = useByYear();
  const { data: paceTrend } = usePaceTrend();

  if (isLoading) return (
    <div style={{ padding: 32 }}>
      <SkeletonStatCards />
      <SkeletonChart height={220} />
      <SkeletonChart height={200} />
    </div>
  );
  if (!summary) return null;

  return (
    <div style={{ padding: 32, color: '#fff' }}>
      <h1 style={{ marginBottom: 24, fontSize: 24, fontWeight: 700 }}>Dashboard</h1>

      {/* Stat cards */}
      <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 40 }}>
        <StatCard label="Total Runs" value={summary.total_runs.toLocaleString()} />
        <StatCard label="Total Distance" value={`${summary.total_distance_miles.toLocaleString()} mi`} />
        <StatCard label="Total Time" value={`${summary.total_time_hours.toLocaleString()} hrs`} />
        <StatCard label="Elevation" value={`${summary.total_elevation_ft.toLocaleString()} ft`} />
        <StatCard label="Years Active" value={summary.years_active} sub={summary.sources.join(', ')} />
      </div>

      {/* Yearly distance bar chart */}
      {byYear && byYear.length > 0 && (
        <div style={{ marginBottom: 40 }}>
          <h2 style={{ fontSize: 16, marginBottom: 16, color: '#ccc' }}>Distance by Year</h2>
          <ResponsiveContainer width="100%" height={220}>
            <BarChart data={byYear} margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
              <XAxis dataKey="year" stroke="#555" tick={{ fill: '#888', fontSize: 12 }} />
              <YAxis stroke="#555" tick={{ fill: '#888', fontSize: 12 }} unit=" mi" />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333', color: '#fff' }}
                formatter={(v: number | undefined) => [v != null ? `${v.toFixed(0)} mi` : v, 'Distance']}
              />
              <Bar dataKey="distance_miles" fill="#e94560" radius={[2, 2, 0, 0]} />
            </BarChart>
          </ResponsiveContainer>
        </div>
      )}

      {/* Pace trend */}
      {paceTrend && paceTrend.length > 0 && (
        <div>
          <h2 style={{ fontSize: 16, marginBottom: 16, color: '#ccc' }}>Pace Trend (monthly avg)</h2>
          <ResponsiveContainer width="100%" height={200}>
            <LineChart data={paceTrend} margin={{ top: 0, right: 16, left: 0, bottom: 0 }}>
              <XAxis dataKey="period" stroke="#555" tick={{ fill: '#888', fontSize: 11 }} interval="preserveStartEnd" />
              <YAxis
                stroke="#555"
                tick={{ fill: '#888', fontSize: 12 }}
                reversed
                tickFormatter={(v) => formatPace(v)}
                domain={['auto', 'auto']}
              />
              <Tooltip
                contentStyle={{ background: '#1a1a2e', border: '1px solid #333', color: '#fff' }}
                formatter={(v: number | undefined) => [v != null ? formatPace(v) : v, 'Avg Pace']}
              />
              <Line type="monotone" dataKey="avg_pace_sec_per_mile" stroke="#e94560" dot={false} strokeWidth={2} />
            </LineChart>
          </ResponsiveContainer>
        </div>
      )}
    </div>
  );
}
