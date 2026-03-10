import { useState } from 'react';
import { useNavigate } from 'react-router-dom';
import { useActivities } from '../hooks/useActivities';
import { SkeletonTableRows } from '../components/Skeleton';
import { formatDate, formatDistance, formatDuration, formatPace, sourceColor } from '../utils';
import type { ActivityFilters } from '../api/activities';

export function Activities() {
  const navigate = useNavigate();
  const [filters, setFilters] = useState<ActivityFilters>({ page: 1, limit: 50, order: 'desc' });
  const { data, isLoading } = useActivities(filters);

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 25 }, (_, i) => currentYear - i);

  return (
    <div style={{ padding: 32, color: '#fff' }}>
      <h1 style={{ marginBottom: 24, fontSize: 24, fontWeight: 700 }}>Activities</h1>

      {/* Filters */}
      <div style={{ display: 'flex', gap: 12, flexWrap: 'wrap', marginBottom: 24 }}>
        <select
          style={selectStyle}
          value={filters.year ?? ''}
          onChange={(e) => setFilters({ ...filters, year: e.target.value ? +e.target.value : undefined, page: 1 })}
        >
          <option value="">All years</option>
          {years.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>

        <select
          style={selectStyle}
          value={filters.source ?? ''}
          onChange={(e) => setFilters({ ...filters, source: e.target.value || undefined, page: 1 })}
        >
          <option value="">All sources</option>
          {['garmin', 'strava', 'nike', 'runkeeper', 'polar', 'suunto'].map((s) => (
            <option key={s} value={s}>{s}</option>
          ))}
        </select>

        <select
          style={selectStyle}
          value={filters.activity_type ?? ''}
          onChange={(e) => setFilters({ ...filters, activity_type: e.target.value || undefined, page: 1 })}
        >
          <option value="">All types</option>
          {['run', 'trail_run', 'treadmill', 'race', 'bike', 'swim', 'walk', 'hike', 'kayak', 'row', 'yoga', 'strength', 'workout', 'other'].map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      {isLoading && (
        <table style={{ width: '100%', borderCollapse: 'collapse' }}>
          <tbody><SkeletonTableRows rows={12} /></tbody>
        </table>
      )}

      {data && (
        <>
          <div style={{ color: '#888', fontSize: 13, marginBottom: 12 }}>
            {data.total.toLocaleString()} activities
          </div>

          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ color: '#666', borderBottom: '1px solid #333' }}>
                <th style={th}>Date</th>
                <th style={th}>Title</th>
                <th style={th}>Distance</th>
                <th style={th}>Duration</th>
                <th style={th}>Pace</th>
                <th style={th}>HR</th>
                <th style={th}>Source</th>
              </tr>
            </thead>
            <tbody>
              {data.items.map((a) => (
                <tr
                  key={a.id}
                  onClick={() => navigate(`/activities/${a.id}`)}
                  style={{ borderBottom: '1px solid #1e1e2e', cursor: 'pointer' }}
                  onMouseEnter={(e) => (e.currentTarget.style.background = '#16213e')}
                  onMouseLeave={(e) => (e.currentTarget.style.background = 'transparent')}
                >
                  <td style={td}>{formatDate(a.start_time)}</td>
                  <td style={td}>{a.title ?? a.activity_type}</td>
                  <td style={td}>{formatDistance(a.distance_miles)}</td>
                  <td style={td}>{formatDuration(a.duration_seconds)}</td>
                  <td style={td}>{formatPace(a.avg_pace_sec_per_mile)}</td>
                  <td style={td}>{a.avg_heart_rate ? `${a.avg_heart_rate} bpm` : '—'}</td>
                  <td style={td}>
                    <span style={{
                      background: sourceColor(a.source), color: '#fff',
                      padding: '2px 8px', borderRadius: 4, fontSize: 11,
                    }}>
                      {a.source}
                    </span>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>

          {/* Pagination */}
          <div style={{ display: 'flex', gap: 8, marginTop: 16, alignItems: 'center' }}>
            <button
              style={btnStyle}
              disabled={filters.page === 1}
              onClick={() => setFilters({ ...filters, page: (filters.page ?? 1) - 1 })}
            >
              Prev
            </button>
            <span style={{ color: '#888', fontSize: 13 }}>Page {filters.page}</span>
            <button
              style={btnStyle}
              disabled={(filters.page ?? 1) * (filters.limit ?? 50) >= data.total}
              onClick={() => setFilters({ ...filters, page: (filters.page ?? 1) + 1 })}
            >
              Next
            </button>
          </div>
        </>
      )}
    </div>
  );
}

const selectStyle: React.CSSProperties = {
  background: '#16213e', color: '#ccc', border: '1px solid #333',
  padding: '6px 12px', borderRadius: 4, fontSize: 13,
};

const th: React.CSSProperties = {
  textAlign: 'left', padding: '8px 12px', fontWeight: 400,
};

const td: React.CSSProperties = {
  padding: '10px 12px', color: '#ccc',
};

const btnStyle: React.CSSProperties = {
  background: '#16213e', color: '#ccc', border: '1px solid #333',
  padding: '6px 16px', borderRadius: 4, cursor: 'pointer', fontSize: 13,
};
