interface Props {
  label: string;
  value: string | number;
  sub?: string;
}

export function StatCard({ label, value, sub }: Props) {
  return (
    <div style={{
      background: '#16213e', borderRadius: 8, padding: '20px 24px',
      flex: 1, minWidth: 160,
    }}>
      <div style={{ color: '#888', fontSize: 12, textTransform: 'uppercase', letterSpacing: 1 }}>{label}</div>
      <div style={{ color: '#fff', fontSize: 28, fontWeight: 700, margin: '8px 0 4px' }}>{value}</div>
      {sub && <div style={{ color: '#666', fontSize: 12 }}>{sub}</div>}
    </div>
  );
}
