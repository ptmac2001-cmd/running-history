import { useEffect } from 'react';
import { MapContainer, TileLayer, Polyline, useMap } from 'react-leaflet';
import 'leaflet/dist/leaflet.css';
import type { RoutePoint } from '../../types';

interface Props {
  points: RoutePoint[];
}

function FitBounds({ positions }: { positions: [number, number][] }) {
  const map = useMap();
  useEffect(() => {
    if (positions.length > 1) {
      map.fitBounds(positions, { padding: [20, 20] });
    }
  }, [map, positions]);
  return null;
}

export function RouteMap({ points }: Props) {
  if (!points.length) {
    return (
      <div style={{
        height: 300, background: '#16213e', borderRadius: 8,
        display: 'flex', alignItems: 'center', justifyContent: 'center',
        color: '#555', fontSize: 14,
      }}>
        No GPS data for this activity
      </div>
    );
  }

  const positions: [number, number][] = points.map((p) => [p.lat, p.lng]);
  const center = positions[Math.floor(positions.length / 2)];

  return (
    <div style={{ height: 300, borderRadius: 8, overflow: 'hidden' }}>
      <MapContainer center={center} zoom={13} style={{ height: '100%', width: '100%' }} zoomControl>
        <TileLayer
          url="https://{s}.basemaps.cartocdn.com/dark_all/{z}/{x}/{y}{r}.png"
          attribution='&copy; OpenStreetMap &copy; CartoDB'
        />
        <Polyline positions={positions} color="#e94560" weight={3} opacity={0.9} />
        <FitBounds positions={positions} />
      </MapContainer>
    </div>
  );
}
