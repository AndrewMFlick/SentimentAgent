/**
 * ToolTableSkeleton Component
 * 
 * Glass-themed loading skeleton for ToolTable
 * Implements Phase 8 Task 110: Loading Skeletons
 * 
 * Features:
 * - Animated pulse effect for loading state
 * - Matches ToolTable structure and layout
 * - Glass morphism design consistent with UI
 * - Configurable number of rows
 */

interface ToolTableSkeletonProps {
  rows?: number;
}

export const ToolTableSkeleton = ({ rows = 5 }: ToolTableSkeletonProps) => {
  return (
    <div className="space-y-4">
      {/* Search and Filter Skeleton */}
      <div className="flex gap-4 mb-4">
        <div className="flex-1 h-10 bg-white/5 rounded-lg animate-pulse" />
        <div className="w-32 h-10 bg-white/5 rounded-lg animate-pulse" />
        <div className="w-32 h-10 bg-white/5 rounded-lg animate-pulse" />
      </div>

      {/* Table Skeleton */}
      <div className="glass-card overflow-hidden">
        <table className="w-full">
          <thead>
            <tr className="border-b border-glass-border">
              <th className="p-4 text-left">
                <div className="h-4 w-24 bg-white/10 rounded animate-pulse" />
              </th>
              <th className="p-4 text-left">
                <div className="h-4 w-20 bg-white/10 rounded animate-pulse" />
              </th>
              <th className="p-4 text-left">
                <div className="h-4 w-32 bg-white/10 rounded animate-pulse" />
              </th>
              <th className="p-4 text-left">
                <div className="h-4 w-20 bg-white/10 rounded animate-pulse" />
              </th>
              <th className="p-4 text-left">
                <div className="h-4 w-24 bg-white/10 rounded animate-pulse" />
              </th>
            </tr>
          </thead>
          <tbody>
            {Array.from({ length: rows }).map((_, index) => (
              <tr
                key={index}
                className="border-b border-glass-border hover:bg-white/5 transition-colors"
              >
                {/* Tool Name */}
                <td className="p-4">
                  <div className="h-5 w-32 bg-white/10 rounded animate-pulse" />
                </td>
                {/* Vendor */}
                <td className="p-4">
                  <div className="h-4 w-24 bg-white/10 rounded animate-pulse" />
                </td>
                {/* Categories */}
                <td className="p-4">
                  <div className="flex gap-2">
                    <div className="h-6 w-20 bg-white/10 rounded-full animate-pulse" />
                    <div className="h-6 w-24 bg-white/10 rounded-full animate-pulse" />
                  </div>
                </td>
                {/* Status */}
                <td className="p-4">
                  <div className="h-6 w-16 bg-white/10 rounded-full animate-pulse" />
                </td>
                {/* Actions */}
                <td className="p-4">
                  <div className="flex gap-2">
                    <div className="h-8 w-16 bg-white/10 rounded-lg animate-pulse" />
                    <div className="h-8 w-16 bg-white/10 rounded-lg animate-pulse" />
                    <div className="h-8 w-16 bg-white/10 rounded-lg animate-pulse" />
                  </div>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>

      {/* Pagination Skeleton */}
      <div className="flex items-center justify-between mt-4">
        <div className="h-10 w-24 bg-white/5 rounded-lg animate-pulse" />
        <div className="h-4 w-32 bg-white/5 rounded animate-pulse" />
        <div className="h-10 w-24 bg-white/5 rounded-lg animate-pulse" />
      </div>
    </div>
  );
};
