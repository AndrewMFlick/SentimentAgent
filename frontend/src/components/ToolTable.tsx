/**
 * ToolTable Component
 * 
 * Glass-themed table for managing AI tools with search, filter, pagination
 * Updated for Phase 3: Multi-category support, enhanced filters, React Query caching
 */
import { useState, useEffect } from 'react';
import { useQuery } from '@tanstack/react-query';
import { Tool, ToolStatus } from '../types';
import { api } from '../services/api';
import Pagination from './Pagination';

interface ToolTableProps {
  adminToken: string;
  onEdit: (tool: Tool) => void;
  onDelete: (tool: Tool) => void;
  onArchive: (tool: Tool) => void;
  onUnarchive: (tool: Tool) => void;
  onMerge: (tool: Tool, allTools: Tool[]) => void;
  onViewHistory?: (tool: Tool) => void;
  refreshTrigger?: number;
}

export const ToolTable = ({ 
  adminToken, 
  onEdit, 
  onDelete, 
  onArchive, 
  onUnarchive, 
  onMerge,
  onViewHistory,
  refreshTrigger 
}: ToolTableProps) => {
  // Pagination state
  const [currentPage, setCurrentPage] = useState(1);
  const [limit] = useState(20);
  
  // Filter state
  const [searchQuery, setSearchQuery] = useState('');
  const [statusFilter, setStatusFilter] = useState<string>('active');
  const [categoryFilter, setCategoryFilter] = useState<string[]>([]);
  const [vendorFilter] = useState('');  // Future feature
  const [sortBy] = useState('name');    // Future feature
  const [sortOrder] = useState<'asc' | 'desc'>('asc');  // Future feature
  const [debouncedSearch, setDebouncedSearch] = useState('');

  // Debounce search input
  useEffect(() => {
    const timer = setTimeout(() => {
      setDebouncedSearch(searchQuery);
      setCurrentPage(1); // Reset to first page on search
    }, 300);

    return () => clearTimeout(timer);
  }, [searchQuery]);

  // Fetch tools with React Query
  const { data, isLoading, error } = useQuery({
    queryKey: ['admin-tools', currentPage, limit, debouncedSearch, statusFilter, categoryFilter, vendorFilter, sortBy, sortOrder, refreshTrigger],
    queryFn: async () => {
      return await api.listAdminTools(
        {
          page: currentPage,
          limit: limit,
          search: debouncedSearch || undefined,
          status: statusFilter || undefined,
          category: categoryFilter.length > 0 ? categoryFilter : undefined,
          vendor: vendorFilter || undefined,
          sort_by: sortBy,
          sort_order: sortOrder,
        },
        adminToken
      );
    },
    enabled: !!adminToken,
  });

  const tools = data?.tools || [];
  const totalTools = data?.pagination?.total_items || 0;
  const totalPages = data?.pagination?.total_pages || 0;
  const hasNext = data?.pagination?.has_next || false;
  const hasPrev = data?.pagination?.has_prev || false;

  if (isLoading && tools.length === 0) {
    return (
      <div className="flex flex-col items-center py-16 gap-4">
        <div className="border-4 border-dark-elevated border-t-blue-500 rounded-full w-12 h-12 animate-spin"></div>
        <p className="text-gray-300">Loading tools...</p>
      </div>
    );
  }

  return (
    <div className="space-y-4">
      {/* Loading overlay for subsequent fetches */}
      {isLoading && tools.length > 0 && (
        <div className="fixed inset-0 bg-black/50 backdrop-blur-sm z-50 flex items-center justify-center">
          <div className="bg-dark-elevated/90 border border-glass-border rounded-xl p-6 flex flex-col items-center gap-4">
            <div className="border-4 border-dark-elevated border-t-blue-500 rounded-full w-12 h-12 animate-spin"></div>
            <p className="text-gray-300">Updating tools...</p>
          </div>
        </div>
      )}

      {/* Error display */}
      {error && (
        <div className="bg-red-900/20 border border-red-700/50 rounded-lg p-4 flex items-start gap-3">
          <span className="text-red-400 text-xl">⚠️</span>
          <div className="flex-1">
            <h3 className="text-red-300 font-bold mb-1">Error Loading Tools</h3>
            <p className="text-red-200 text-sm">
              {String(error)}
            </p>
          </div>
        </div>
      )}

      {/* Search and Filter Controls */}
      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        {/* Search */}
        <div className="lg:col-span-2">
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

        {/* Status Filter */}
        <div>
          <label htmlFor="status-filter" className="block text-sm font-bold text-gray-200 mb-2">
            Status
          </label>
          <select
            id="status-filter"
            value={statusFilter}
            onChange={(e) => {
              setStatusFilter(e.target.value);
              setCurrentPage(1);
            }}
            className="glass-input w-full"
          >
            <option value="active">Active Only</option>
            <option value="archived">Archived Only</option>
            <option value="all">All Statuses</option>
          </select>
        </div>

        {/* Category Filter */}
        <div>
          <label htmlFor="category-filter" className="block text-sm font-bold text-gray-200 mb-2">
            Category
          </label>
          <select
            id="category-filter"
            value={categoryFilter[0] || ''}
            onChange={(e) => {
              setCategoryFilter(e.target.value ? [e.target.value] : []);
              setCurrentPage(1);
            }}
            className="glass-input w-full"
          >
            <option value="">All Categories</option>
            <option value="code_assistant">Code Assistant</option>
            <option value="autonomous_agent">Autonomous Agent</option>
            <option value="code_review">Code Review</option>
            <option value="testing">Testing</option>
            <option value="devops">DevOps</option>
            <option value="project_management">Project Management</option>
            <option value="collaboration">Collaboration</option>
            <option value="other">Other</option>
          </select>
        </div>
      </div>

      {/* Vendor Filter (optional - can add if needed) */}
      {vendorFilter && (
        <div className="text-xs text-gray-400">
          Filtering by vendor: {vendorFilter}
        </div>
      )}

      {/* Results Summary */}
      <div className="flex justify-between items-center text-sm text-gray-400">
        <span>
          Showing {tools.length > 0 ? (currentPage - 1) * limit + 1 : 0} - {Math.min(currentPage * limit, totalTools)} of {totalTools} tools
        </span>
        <span className="text-xs">
          Page {currentPage} of {totalPages || 1}
        </span>
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
                    <div className="flex flex-wrap gap-1">
                      {tool.categories.map((category: string, idx: number) => (
                        <span
                          key={idx}
                          className="inline-block px-3 py-1 bg-blue-900/40 border border-blue-700/50 rounded-full text-xs font-bold text-blue-300"
                        >
                          {category.replace(/_/g, ' ').replace(/\b\w/g, (l: string) => l.toUpperCase())}
                        </span>
                      ))}
                    </div>
                  </td>
                  <td className="p-4 text-sm text-gray-300">
                    <span
                      className={`inline-block px-3 py-1 rounded-full text-xs font-bold ${
                        tool.status === ToolStatus.ACTIVE
                          ? 'bg-emerald-900/40 border border-emerald-700/50 text-emerald-300'
                          : 'bg-gray-900/40 border border-gray-700/50 text-gray-300'
                      }`}
                    >
                      {tool.status === ToolStatus.ACTIVE ? 'Active' : 'Archived'}
                    </span>
                  </td>
                  <td className="p-4 text-sm text-gray-300">
                    <div className="flex gap-2 flex-wrap">
                      <button
                        onClick={() => onEdit(tool)}
                        className="px-3 py-1.5 text-xs font-bold bg-blue-900/40 text-blue-300 border border-blue-700/50 rounded-lg transition-all hover:bg-blue-900/60 hover:border-blue-600/60"
                        title="Edit tool"
                      >
                        ✏️ Edit
                      </button>
                      {tool.status === ToolStatus.ACTIVE && (
                        <>
                          <button
                            onClick={() => onMerge(tool, tools)}
                            className="px-3 py-1.5 text-xs font-bold bg-purple-900/40 text-purple-300 border border-purple-700/50 rounded-lg transition-all hover:bg-purple-900/60 hover:border-purple-600/60"
                            title="Merge tools into this one"
                          >
                            🔗 Merge
                          </button>
                          {onViewHistory && (
                            <button
                              onClick={() => onViewHistory(tool)}
                              className="px-3 py-1.5 text-xs font-bold bg-indigo-900/40 text-indigo-300 border border-indigo-700/50 rounded-lg transition-all hover:bg-indigo-900/60 hover:border-indigo-600/60"
                              title="View merge history"
                            >
                              📜 History
                            </button>
                          )}
                        </>
                      )}
                      {tool.status === ToolStatus.ACTIVE ? (
                        <button
                          onClick={() => onArchive(tool)}
                          className="px-3 py-1.5 text-xs font-bold bg-yellow-900/40 text-yellow-300 border border-yellow-700/50 rounded-lg transition-all hover:bg-yellow-900/60 hover:border-yellow-600/60"
                          title="Archive tool"
                        >
                          📦 Archive
                        </button>
                      ) : (
                        <button
                          onClick={() => onUnarchive(tool)}
                          className="px-3 py-1.5 text-xs font-bold bg-emerald-900/40 text-emerald-300 border border-emerald-700/50 rounded-lg transition-all hover:bg-emerald-900/60 hover:border-emerald-600/60"
                          title="Unarchive tool"
                        >
                          ↩️ Unarchive
                        </button>
                      )}
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
      <Pagination
        currentPage={currentPage}
        totalPages={totalPages}
        hasNext={hasNext}
        hasPrev={hasPrev}
        onPageChange={setCurrentPage}
        className="mt-6"
      />
    </div>
  );
};
