interface SkeletonProps {
  className?: string;
  style?: React.CSSProperties;
}

export function Skeleton({ className = '', style }: SkeletonProps) {
  return (
    <div
      className={`animate-pulse rounded ${className}`}
      style={{ backgroundColor: '#e2e8f0', ...style }}
    />
  );
}

export function CardSkeleton() {
  return (
    <div className="bg-white border border-[#e2e8f0] rounded-xl shadow-sm p-5 space-y-4">
      <Skeleton className="h-4 w-1/3" />
      <Skeleton className="h-8 w-1/2" />
      <Skeleton className="h-3 w-2/3" />
    </div>
  );
}

export function ChartSkeleton() {
  return (
    <div className="bg-white border border-[#e2e8f0] rounded-xl shadow-sm p-5 space-y-4">
      <Skeleton className="h-5 w-1/4" />
      <div className="flex items-end gap-2 h-48">
        {[...Array(12)].map((_, i) => (
          <Skeleton key={i} className="flex-1" style={{ height: `${Math.random() * 60 + 40}%` }} />
        ))}
      </div>
    </div>
  );
}
