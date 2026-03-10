interface SkeletonProps {
  width?: string | number;
  height?: string | number;
  style?: React.CSSProperties;
}

export function Skeleton({ width = '100%', height = 16, style }: SkeletonProps) {
  return <div className="skeleton" style={{ width, height, ...style }} />;
}

export function SkeletonStatCards() {
  return (
    <div style={{ display: 'flex', gap: 16, flexWrap: 'wrap', marginBottom: 40 }}>
      {Array.from({ length: 5 }).map((_, i) => (
        <div key={i} style={{ background: '#1a1a2e', borderRadius: 8, padding: '20px 24px', minWidth: 140 }}>
          <Skeleton height={12} width={80} style={{ marginBottom: 12 }} />
          <Skeleton height={28} width={100} />
        </div>
      ))}
    </div>
  );
}

export function SkeletonChart({ height = 220 }: { height?: number }) {
  return <Skeleton width="100%" height={height} style={{ borderRadius: 8, marginBottom: 40 }} />;
}

export function SkeletonTableRows({ rows = 10 }: { rows?: number }) {
  return (
    <>
      {Array.from({ length: rows }).map((_, i) => (
        <tr key={i}>
          {Array.from({ length: 7 }).map((_, j) => (
            <td key={j} style={{ padding: '10px 12px' }}>
              <Skeleton height={12} width={j === 1 ? 120 : 60} />
            </td>
          ))}
        </tr>
      ))}
    </>
  );
}
