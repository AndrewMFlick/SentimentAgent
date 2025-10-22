import { useState, useEffect } from 'react';

interface PaginationProps {
  currentPage: number;
  totalPages: number;
  hasNext: boolean;
  hasPrev: boolean;
  onPageChange: (page: number) => void;
  className?: string;
}

export default function Pagination({
  currentPage,
  totalPages,
  hasNext,
  hasPrev,
  onPageChange,
  className = ''
}: PaginationProps) {
  const [pageInput, setPageInput] = useState(currentPage.toString());

  useEffect(() => {
    setPageInput(currentPage.toString());
  }, [currentPage]);

  const handlePageInputChange = (e: React.ChangeEvent<HTMLInputElement>) => {
    setPageInput(e.target.value);
  };

  const handlePageInputSubmit = (e: React.FormEvent) => {
    e.preventDefault();
    const page = parseInt(pageInput, 10);
    if (page >= 1 && page <= totalPages) {
      onPageChange(page);
    } else {
      setPageInput(currentPage.toString());
    }
  };

  const handlePrevious = () => {
    if (hasPrev) {
      onPageChange(currentPage - 1);
    }
  };

  const handleNext = () => {
    if (hasNext) {
      onPageChange(currentPage + 1);
    }
  };

  const handleFirst = () => {
    if (currentPage !== 1) {
      onPageChange(1);
    }
  };

  const handleLast = () => {
    if (currentPage !== totalPages) {
      onPageChange(totalPages);
    }
  };

  if (totalPages <= 1) {
    return null;
  }

  return (
    <div className={`flex items-center justify-between gap-4 ${className}`}>
      {/* Page info */}
      <div className="text-sm text-gray-400">
        Page <span className="font-bold text-white">{currentPage}</span> of{' '}
        <span className="font-bold text-white">{totalPages}</span>
      </div>

      {/* Navigation controls */}
      <div className="flex items-center gap-2">
        {/* First page */}
        <button
          onClick={handleFirst}
          disabled={!hasPrev}
          className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
            hasPrev
              ? 'bg-blue-900/40 text-blue-300 border border-blue-700/50 hover:bg-blue-900/60 hover:border-blue-600/60'
              : 'bg-gray-900/20 text-gray-600 border border-gray-800/30 cursor-not-allowed'
          }`}
          title="First page"
        >
          ⏮️ First
        </button>

        {/* Previous page */}
        <button
          onClick={handlePrevious}
          disabled={!hasPrev}
          className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
            hasPrev
              ? 'bg-blue-900/40 text-blue-300 border border-blue-700/50 hover:bg-blue-900/60 hover:border-blue-600/60'
              : 'bg-gray-900/20 text-gray-600 border border-gray-800/30 cursor-not-allowed'
          }`}
          title="Previous page"
        >
          ◀️ Previous
        </button>

        {/* Page input */}
        <form onSubmit={handlePageInputSubmit} className="flex items-center gap-2">
          <label htmlFor="page-input" className="text-xs text-gray-400">Go to:</label>
          <input
            id="page-input"
            type="number"
            min="1"
            max={totalPages}
            value={pageInput}
            onChange={handlePageInputChange}
            className="w-16 px-2 py-1.5 text-xs font-bold text-center bg-dark-elevated/50 border border-glass-border rounded-lg text-white focus:outline-none focus:ring-2 focus:ring-blue-500/50 focus:border-blue-500/50"
            aria-label="Page number"
          />
          <button
            type="submit"
            className="px-3 py-1.5 text-xs font-bold bg-blue-900/40 text-blue-300 border border-blue-700/50 rounded-lg transition-all hover:bg-blue-900/60 hover:border-blue-600/60"
          >
            Go
          </button>
        </form>

        {/* Next page */}
        <button
          onClick={handleNext}
          disabled={!hasNext}
          className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
            hasNext
              ? 'bg-blue-900/40 text-blue-300 border border-blue-700/50 hover:bg-blue-900/60 hover:border-blue-600/60'
              : 'bg-gray-900/20 text-gray-600 border border-gray-800/30 cursor-not-allowed'
          }`}
          title="Next page"
        >
          Next ▶️
        </button>

        {/* Last page */}
        <button
          onClick={handleLast}
          disabled={!hasNext}
          className={`px-3 py-1.5 text-xs font-bold rounded-lg transition-all ${
            hasNext
              ? 'bg-blue-900/40 text-blue-300 border border-blue-700/50 hover:bg-blue-900/60 hover:border-blue-600/60'
              : 'bg-gray-900/20 text-gray-600 border border-gray-800/30 cursor-not-allowed'
          }`}
          title="Last page"
        >
          Last ⏭️
        </button>
      </div>
    </div>
  );
}
