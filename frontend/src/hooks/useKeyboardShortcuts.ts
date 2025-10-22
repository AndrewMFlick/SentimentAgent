/**
 * useKeyboardShortcuts Hook
 * 
 * Custom hook for handling keyboard shortcuts
 * Implements Phase 8 Task 113: Keyboard Shortcuts
 * 
 * Features:
 * - Ctrl/Cmd + F: Focus search
 * - Esc: Close modals
 * - Ctrl/Cmd + N: New tool (admin)
 * - Customizable shortcuts per component
 */
import { useEffect, useCallback } from 'react';

interface ShortcutHandler {
  key: string;
  ctrl?: boolean;
  shift?: boolean;
  alt?: boolean;
  handler: (e: KeyboardEvent) => void;
  description: string;
}

export const useKeyboardShortcuts = (shortcuts: ShortcutHandler[]) => {
  const handleKeyDown = useCallback(
    (e: KeyboardEvent) => {
      for (const shortcut of shortcuts) {
        const ctrlKey = e.ctrlKey || e.metaKey; // Support both Ctrl and Cmd
        const matchesKey = e.key.toLowerCase() === shortcut.key.toLowerCase();
        const matchesCtrl = shortcut.ctrl === undefined || shortcut.ctrl === ctrlKey;
        const matchesShift = shortcut.shift === undefined || shortcut.shift === e.shiftKey;
        const matchesAlt = shortcut.alt === undefined || shortcut.alt === e.altKey;

        if (matchesKey && matchesCtrl && matchesShift && matchesAlt) {
          e.preventDefault();
          shortcut.handler(e);
          return;
        }
      }
    },
    [shortcuts]
  );

  useEffect(() => {
    document.addEventListener('keydown', handleKeyDown);
    return () => {
      document.removeEventListener('keydown', handleKeyDown);
    };
  }, [handleKeyDown]);
};

/**
 * Common keyboard shortcuts for admin panel
 */
export const adminShortcuts = {
  search: { key: 'f', ctrl: true, description: 'Focus search' },
  newTool: { key: 'n', ctrl: true, description: 'Create new tool' },
  escape: { key: 'Escape', description: 'Close modal/dialog' },
  refresh: { key: 'r', ctrl: true, description: 'Refresh list' },
  help: { key: '?', shift: true, description: 'Show keyboard shortcuts' },
} as const;
