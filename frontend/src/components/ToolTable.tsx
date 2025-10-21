/**
 * ToolTable Component
 * 
 * Glass-themed table for managing AI tools with search, filter, pagination
 */
import { useState, useEffect } from 'react';

interface Tool {
  id: string;
  name: string;
  slug: string;
  vendor: string;
  category: string;
  description: string;
  status: string;
  created_at: string;
  updated_at: string;
}

interface ToolTableProps {
  adminToken: string;
  onEdit: (tool: Tool) => void;
  onDelete: (tool: Tool) => void;
  refreshTrigger?: number;
}

export const ToolTable = ({ adminToken, onEdit, onDelete, refreshTrigger }: ToolTableProps) => {
  const [tools, setTools] = useState<Tool[]>([]);
  const [loading, setLoading] = useState(false);
  const [error, setError] = useState<string | null>(null);
  
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [totalTools, setTotalTools] = useState(0);
  const [limit] = useState(20);
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [categoryFilter, setCategoryFilter] = useState('');
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(1); // Reset to first page on search
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch tools
  useEffect(() => {
    const fetchTools = async () => {
      setLoading(true);
      setError(null);

      try {
        const params = new URLSearchParams({
          page: currentPage.toString(),
          limit: limit.toString(),
        });

        if (debouncedSearch) {
          params.append('search', debouncedSearch);
        }

        if (categoryFilter) {
          params.append('category', categoryFilter);
        }

        const response = await fetch(
          `http://localhost:8000/api/admin/tools?${params.toString()}`,
          {
            headers: {
              'X-Admin-Token': adminToken,
            },
          }
        );

        if (!response.ok) {
          throw new Error(`Failed to fetch tools: ${response.statusText}`);
        }

        const data = await response.json();
        setTools(data.tools || []);
        setTotalTools(data.total || 0);
      } catch (err) {
        const message = err instanceof Error ? err.message : 'Failed to fetch tools';
        setError(message);
        console.error('Error fetching tools:', err);
      } finally {
        setLoading(false);
      }
    };

    fetchTools();
  }, [adminToken, currentPage, limit, debouncedSearch, categoryFilter, refreshTrigger]);

  const totalPages = Math.ceil(totalTools / limit);

  const handlePreviousPage = () => {
    if (currentPage > 1) {
      setCurrentPage(currentPage - 1);
    }
  };

  const handleNextPage = () => {
    if (currentPage < totalPages) {
      setCurrentPage(currentPage + 1);
    }
  };

  if (loading && tools.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 gap-4">
        <div className="border-4 border-dark-elevated border-t-blue-500 rounded-full w-12 h-12 animate-spin"></div>
        <p className="text-gray-300">Loading tools...</p>
      </div>
    );
  }

  if (error) {
    return (
      <div className="p-4 bg-red-900/30 border border-red-700/50 rounded-lg text-red-300">
        <strong>Error:</strong> {error}
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Search and Filter Controls */}
      <div className="flex flex-col md:flex-row gap-4">
        <div className="flex-1">
          <label htmlFor="search-tools" className="block text-sm font-bold text-gray-200 mb-2">
            Search Tools
          </label>
          <input
            id="search-tools"
            type="text"
            value={searchQuery}
            onChange={(e) => setSearchQuery(e.target.value)}
            placeholder="Search by name..."
            className="glass-input w-full"
          />
        </div>

        <div className="w-full md:w-64">
          <label htmlFor="category-filter" className="block text-sm font-bold text-gray-200 mb-2">
            Category
          </label>
          <select
            id="category-filter"
            value={categoryFilter}
            onChange={(e) => {
              setCategoryFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="glass-input w-full"
          >
            <option value="">All Categories</option>
            <option value="code-completion">Code Completion</option>
            <option value="chat">Chat</option>
            <option value="analysis">Analysis</option>
          </select>
        </div>
      </div>

      {/* Results Summary */}
      <div className="text-sm text-gray-400">
        Showing {tools.length > 0 ? (currentPage - 1) * limit + 1 : 0} - {Math.min(currentPage * limit, totalTools)} of {totalTools} tools
      </div>

      {/* Table */}
      {tools.length === 0 ? (
        <div className="text-center py-20 px-5">
          <p className="text-xl text-gray-300 mb-2">No tools found</p>
          <p className="text-sm text-gray-500">
            {debouncedSearch || categoryFilter
              ? 'Try adjusting your search or filter criteria'
              : 'Add your first tool to get started'}
          </p>
        </div>
      ) : (
        <div className="overflow-x-auto">
          <table className="w-full border-collapse">
            <thead>
              <tr>
                <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">
                  Tool Name
                </th>
                <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">
                  Vendor
                </th>
                <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">
                  Category
                </th>
                <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">
                  Status
                </th>
                <th className="text-left p-4 bg-dark-elevated/70 border-b-2 border-glass-border-strong text-sm font-bold text-gray-200">
                  Actions
                </th>
              </tr>
            </thead>
            <tbody>
              {tools.map((tool) => (
                <tr
                  key={tool.id}
                  className="border-b border-glass-border hover:bg-dark-elevated/30 transition-colors"
                >
                  <td className="p-4 text-sm text-gray-200">
                    <strong className="text-white">{tool.name}</strong>
                    {tool.description && (
                      <div className="text-xs text-gray-500 mt-1 line-clamp-2">
                        {tool.description}
                      </div>
                    )}
                  </td>
                  <td className="p-4 text-sm text-gray-300">{tool.vendor}</td>
                  <td className="p-4 text-sm text-gray-300">
                    <span className="inline-block px-3 py-1 bg-blue-900/40 border border-blue-700/50 rounded-full text-xs font-bold text-blue-300">
                      {tool.category}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-300">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                        tool.status === 'active'
                          ? 'bg-emerald-900/40 border border-emerald-700/50 text-emerald-300'
                          : tool.status === 'deprecated'
                          ? 'bg-yellow-900/40 border border-yellow-700/50 text-yellow-300'
                          : 'bg-red-900/40 border border-red-700/50 text-red-300'
                      }`}
                    >
                      {tool.status}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-300">
                    <div className="flex gap-2">
                      <button
                        onClick={() => onEdit(tool)}
                        className="px-3 py-1.5 text-xs font-bold bg-blue-900/40 text-blue-300 border border-blue-700/50 rounded-lg transition-all hover:bg-blue-900/60 hover:border-blue-600/60"
                        title="Edit tool"
                      >
                        ✏️ Edit
                      </button>
                      <button
                        onClick={() => onDelete(tool)}
                        className="px-3 py-1.5 text-xs font-bold bg-red-900/40 text-red-300 border border-red-700/50 rounded-lg transition-all hover:bg-red-900/60 hover:border-red-600/60"
                        title="Delete tool"
                      >
                        🗑️ Delete
                      </button>
                    </div>
                  </td>
                </tr>
              ))}
            </tbody>
          </table>
        </div>
      )}

      {/* Pagination Controls */}
      {totalPages > 1 && (
        <div className="flex justify-between items-center mt-6">
          <button
            onClick={handlePreviousPage}
            disabled={currentPage === 1 || loading}
            className="glass-button disabled:opacity-50 disabled:cursor-not-allowed"
          >
            ← Previous
          </button>

          <span className="text-sm text-gray-300">
            Page {currentPage} of {totalPages}
          </span>

          <button
            onClick={handleNextPage}
            disabled={currentPage >= totalPages || loading}
            className="glass-button disabled:opacity-50 disabled:cursor-not-allowed"
          >
            Next →
          </button>
        </div>
      )}
    </div>
  );
};
