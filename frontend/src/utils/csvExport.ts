/**
 * CSV Export Utility
 * 
 * Implements Phase 8 Task 114: CSV export functionality for tool list
 * 
 * Features:
 * - Export tool list to CSV format
 * - Include all tool metadata (name, vendor, categories, status, etc.)
 * - Configurable columns
 * - Proper CSV formatting and escaping
 */

import { Tool } from '../types';

export interface CSVExportOptions {
  /**
   * Columns to include in export
   * @default ['name', 'vendor', 'categories', 'status', 'description', 'created_at', 'updated_at']
   */
  columns?: string[];
  
  /**
   * Filename for downloaded file
   * @default 'tools-export-{timestamp}.csv'
   */
  filename?: string;
  
  /**
   * Include header row
   * @default true
   */
  includeHeader?: boolean;
}

/**
 * Escape CSV field value
 */
function escapeCSVField(value: any): string {
  if (value === null || value === undefined) {
    return '';
  }
  
  // Convert to string
  let str = String(value);
  
  // If field contains comma, quote, or newline, wrap in quotes and escape quotes
  if (str.includes(',') || str.includes('"') || str.includes('\n')) {
    str = '"' + str.replace(/"/g, '""') + '"';
  }
  
  return str;
}

/**
 * Format tool data for CSV export
 */
function formatToolForCSV(tool: Tool, columns: string[]): string[] {
  const fieldMap: Record<string, any> = {
    id: tool.id,
    name: tool.name,
    slug: tool.slug,
    vendor: tool.vendor,
    categories: Array.isArray(tool.categories) ? tool.categories.join('; ') : tool.categories,
    status: tool.status,
    description: tool.description || '',
    merged_into: tool.merged_into || '',
    created_at: tool.created_at || '',
    updated_at: tool.updated_at || '',
    created_by: tool.created_by || '',
    updated_by: tool.updated_by || ''
  };
  
  return columns.map(col => escapeCSVField(fieldMap[col] || ''));
}

/**
 * Export tools to CSV
 */
export function exportToolsToCSV(tools: Tool[], options: CSVExportOptions = {}): void {
  const {
    columns = ['name', 'vendor', 'categories', 'status', 'description', 'created_at', 'updated_at'],
    filename = `tools-export-${new Date().toISOString().split('T')[0]}.csv`,
    includeHeader = true
  } = options;
  
  if (tools.length === 0) {
    throw new Error('No tools to export');
  }
  
  // Build CSV content
  const rows: string[] = [];
  
  // Add header row
  if (includeHeader) {
    const header = columns.map(col => {
      // Convert snake_case to Title Case
      return col
        .split('_')
        .map(word => word.charAt(0).toUpperCase() + word.slice(1))
        .join(' ');
    });
    rows.push(header.join(','));
  }
  
  // Add data rows
  for (const tool of tools) {
    const row = formatToolForCSV(tool, columns);
    rows.push(row.join(','));
  }
  
  const csvContent = rows.join('\n');
  
  // Create blob and download
  const blob = new Blob([csvContent], { type: 'text/csv;charset=utf-8;' });
  const link = document.createElement('a');
  const url = URL.createObjectURL(blob);
  
  link.setAttribute('href', url);
  link.setAttribute('download', filename);
  link.style.visibility = 'hidden';
  
  document.body.appendChild(link);
  link.click();
  document.body.removeChild(link);
  
  // Clean up
  URL.revokeObjectURL(url);
}

/**
 * Export filtered tools with metadata
 */
export interface FilteredExportOptions extends CSVExportOptions {
  /**
   * Filter criteria used (for filename)
   */
  filters?: {
    status?: string;
    categories?: string[];
    vendor?: string;
    search?: string;
  };
}

export function exportFilteredTools(tools: Tool[], options: FilteredExportOptions = {}): void {
  const { filters, ...csvOptions } = options;
  
  // Generate descriptive filename based on filters
  let filename = 'tools-export';
  
  if (filters) {
    if (filters.status && filters.status !== 'all') {
      filename += `-${filters.status}`;
    }
    if (filters.vendor) {
      filename += `-${filters.vendor.toLowerCase().replace(/\s+/g, '-')}`;
    }
    if (filters.categories && filters.categories.length > 0) {
      filename += `-${filters.categories.join('-')}`;
    }
    if (filters.search) {
      filename += `-search`;
    }
  }
  
  filename += `-${new Date().toISOString().split('T')[0]}.csv`;
  
  exportToolsToCSV(tools, {
    ...csvOptions,
    filename
  });
}

/**
 * Get available export columns with descriptions
 */
export function getAvailableColumns(): Array<{ key: string; label: string; description: string }> {
  return [
    { key: 'id', label: 'ID', description: 'Unique tool identifier' },
    { key: 'name', label: 'Name', description: 'Tool name' },
    { key: 'slug', label: 'Slug', description: 'URL-friendly identifier' },
    { key: 'vendor', label: 'Vendor', description: 'Tool vendor/creator' },
    { key: 'categories', label: 'Categories', description: 'Tool categories (semicolon-separated)' },
    { key: 'status', label: 'Status', description: 'Active or archived' },
    { key: 'description', label: 'Description', description: 'Tool description' },
    { key: 'merged_into', label: 'Merged Into', description: 'Tool ID if merged' },
    { key: 'created_at', label: 'Created At', description: 'Creation timestamp' },
    { key: 'updated_at', label: 'Updated At', description: 'Last update timestamp' },
    { key: 'created_by', label: 'Created By', description: 'Creator user ID' },
    { key: 'updated_by', label: 'Updated By', description: 'Last updater user ID' }
  ];
}
