import { useParams } from 'react-router-dom';
import { useQuery } from '@tanstack/react-query';
import { fetchActivityRoute } from '../api/routes';
import { useActivity } from '../hooks/useActivities';
import { RouteMap } from '../components/maps/RouteMap';
import { formatDate, formatDistance, formatDuration, formatPace, sourceColor } from '../utils';

export function ActivityDetail() {
  const { id } = useParams<{ id: string }>();
  const activityId = Number(id);

  const { data: activity, isLoading } = useActivity(activityId);
  const { data: routeData } = useQuery({
    queryKey: ['route', activityId],
    queryFn: () => fetchActivityRoute(activityId),
    enabled: !!activityId,
  });

  if (isLoading) return <div style={{ color: '#888', padding: 40 }}>Loading...</div>;
  if (!activity) return <div style={{ color: '#888', padding: 40 }}>Activity not found</div>;

  const stats: [string, string][] = [
    ['Date', formatDate(activity.start_time)],
    ['Distance', formatDistance(activity.distance_miles)],
    ['Duration', formatDuration(activity.duration_seconds)],
    ['Moving Time', activity.moving_time_seconds ? formatDuration(activity.moving_time_seconds) : '—'],
    ['Avg Pace', formatPace(activity.avg_pace_sec_per_mile)],
    ['Avg Heart Rate', activity.avg_heart_rate ? `${activity.avg_heart_rate} bpm` : '—'],
    ['Max Heart Rate', activity.max_heart_rate ? `${activity.max_heart_rate} bpm` : '—'],
    ['Elevation Gain', activity.elevation_gain_feet ? `${activity.elevation_gain_feet.toFixed(0)} ft` : '—'],
    ['Calories', activity.calories ? activity.calories.toString() : '—'],
    ['Cadence', activity.avg_cadence ? `${activity.avg_cadence} spm` : '—'],
    ['Gear', activity.gear_name ?? '—'],
    ['Source', activity.source],
  ];

  return (
    <div style={{ padding: 32, color: '#fff', maxWidth: 900 }}>
      <h1 style={{ fontSize: 22, marginBottom: 8 }}>
        {activity.title ?? activity.activity_type}
        <span style={{
          marginLeft: 12, background: sourceColor(activity.source), color: '#fff',
          padding: '2px 10px', borderRadius: 4, fontSize: 12, fontWeight: 400,
        }}>
          {activity.source}
        </span>
      </h1>
      <div style={{ color: '#888', marginBottom: 24 }}>{formatDate(activity.start_time)}</div>

      {/* Map */}
      <div style={{ marginBottom: 32 }}>
        <RouteMap points={routeData?.points ?? []} />
      </div>

      {/* Stats grid */}
      <div style={{
        display: 'grid', gridTemplateColumns: 'repeat(auto-fill, minmax(200px, 1fr))',
        gap: 1, background: '#333', borderRadius: 8, overflow: 'hidden', marginBottom: 32,
      }}>
        {stats.map(([label, value]) => (
          <div key={label} style={{ background: '#16213e', padding: '14px 18px' }}>
            <div style={{ color: '#666', fontSize: 11, textTransform: 'uppercase', marginBottom: 4 }}>{label}</div>
            <div style={{ color: '#fff', fontSize: 15 }}>{value}</div>
          </div>
        ))}
      </div>

      {/* Laps */}
      {activity.laps.length > 0 && (
        <div>
          <h2 style={{ fontSize: 16, marginBottom: 12, color: '#ccc' }}>Laps</h2>
          <table style={{ width: '100%', borderCollapse: 'collapse', fontSize: 13 }}>
            <thead>
              <tr style={{ color: '#666', borderBottom: '1px solid #333' }}>
                <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 400 }}>Lap</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 400 }}>Distance</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 400 }}>Time</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 400 }}>Pace</th>
                <th style={{ textAlign: 'left', padding: '8px 12px', fontWeight: 400 }}>HR</th>
              </tr>
            </thead>
            <tbody>
              {activity.laps.map((lap) => (
                <tr key={lap.lap_number} style={{ borderBottom: '1px solid #1e1e2e' }}>
                  <td style={{ padding: '10px 12px', color: '#ccc' }}>{lap.lap_number}</td>
                  <td style={{ padding: '10px 12px', color: '#ccc' }}>{lap.distance_miles ? formatDistance(lap.distance_miles) : '—'}</td>
                  <td style={{ padding: '10px 12px', color: '#ccc' }}>{lap.duration_seconds ? formatDuration(lap.duration_seconds) : '—'}</td>
                  <td style={{ padding: '10px 12px', color: '#ccc' }}>{formatPace(lap.avg_pace_sec_per_mile)}</td>
                  <td style={{ padding: '10px 12px', color: '#ccc' }}>{lap.avg_heart_rate ? `${lap.avg_heart_rate} bpm` : '—'}</td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {activity.notes && (
        <div style={{ marginTop: 24, background: '#16213e', borderRadius: 8, padding: '16px 20px' }}>
          <div style={{ color: '#666', fontSize: 12, marginBottom: 8 }}>Notes</div>
          <div style={{ color: '#ccc', fontSize: 14 }}>{activity.notes}</div>
        </div>
      )}
    </div>
  );
}
