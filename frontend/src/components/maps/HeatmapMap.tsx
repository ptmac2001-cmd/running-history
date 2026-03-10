import { useState } from 'react';
import { MapContainer, TileLayer, Polyline } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import { useQuery } from '@tanstack/react-query';
import { fetchAllTracks } from '../../api/routes';

export function HeatmapMap() {
  const [year, setYear] = useState<number | undefined>(undefined);
  const { data, isLoading } = useQuery({
    queryKey: ['all-tracks', year],
    queryFn: () => fetchAllTracks(year),
    staleTime: 5 * 60 * 1000,
  });

  const currentYear = new Date().getFullYear();
  const years = Array.from({ length: 25 }, (_, i) => currentYear - i);

  return (
    <div style={{ height: '100vh', display: 'flex', flexDirection: 'column' }}>
      {/* Controls */}
      <div style={{
        background: '#1a1a2e', padding: '12px 20px', display: 'flex',
        gap: 12, alignItems: 'center', zIndex: 1000,
      }}>
        <span style={{ color: '#888', fontSize: 13 }}>Filter by year:</span>
        <select
          style={{ background: '#16213e', color: '#ccc', border: '1px solid #333', padding: '4px 10px', borderRadius: 4, fontSize: 13 }}
          value={year ?? ''}
          onChange={(e) => setYear(e.target.value ? +e.target.value : undefined)}
        >
          <option value="">All years</option>
          {years.map((y) => <option key={y} value={y}>{y}</option>)}
        </select>
        {isLoading && <span style={{ color: '#888', fontSize: 12 }}>Loading tracks...</span>}
        {data && <span style={{ color: '#555', fontSize: 12 }}>{data.tracks.length} routes</span>}
      </div>

      {/* Map */}
      <div style={{ flex: 1 }}>
        <MapContainer
          center={[39.5, -98.35]}
          zoom={4}
          style={{ height: '100%', width: '100%' }}
        >
          <TileLayer
            url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
            attribution='&copy; OpenStreetMap &copy; CartoDB'
          />
          {data?.tracks.map((track) => (
            <Polyline
              key={track.activity_id}
              positions={track.points as [number, number][]}
              color="#e94560"
              weight={1.5}
              opacity={0.4}
            />
          ))}
        </MapContainer>
      </div>
    </div>
  );
}
