export function formatPace(secPerMile: number | null | undefined): string {
  if (!secPerMile) return '—';
  const m = Math.floor(secPerMile / 60);
  const s = Math.round(secPerMile % 60);
  return `${m}:${s.toString().padStart(2, '0')}/mi`;
}

export function formatDuration(seconds: number): string {
  const h = Math.floor(seconds / 3600);
  const m = Math.floor((seconds % 3600) / 60);
  const s = seconds % 60;
  if (h > 0) return `${h}h ${m}m`;
  return `${m}m ${s}s`;
}

export function formatDistance(miles: number): string {
  return `${miles.toFixed(2)} mi`;
}

export function formatDate(isoString: string): string {
  return new Date(isoString).toLocaleDateString('en-US', {
    year: 'numeric', month: 'short', day: 'numeric',
  });
}

export function sourceColor(source: string): string {
  const colors: Record<string, string> = {
    garmin: '#00b2ff',
    strava: '#fc4c02',
    nike: '#111',
    runkeeper: '#4fc3f7',
    polar: '#d32f2f',
    suunto: '#1565c0',
  };
  return colors[source] ?? '#888';
}
