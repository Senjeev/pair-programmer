// src/hooks/useDebouncedTyping.ts
import { useRef, useCallback } from "react";

/**
 * useDebouncedTyping
 * - manages a typing timeout and calls onIdle(editor) when user stops typing
 * - also calls sendTyping(true) immediately and sendTyping(false) after idle
 */
export function useDebouncedTyping(
  sendTyping: (isTyping: boolean) => void,
  onIdle: (editorInstance: any) => void,
  delay = 400
) {
  const timeoutRef = useRef<number | null>(null);

  const handleEdit = useCallback(
    (editorInstance: any) => {
      // user started typing
      sendTyping(true);

      if (timeoutRef.current) {
        window.clearTimeout(timeoutRef.current);
      }

      timeoutRef.current = window.setTimeout(() => {
        sendTyping(false);
        onIdle(editorInstance);
        timeoutRef.current = null;
      }, delay);
    },
    [sendTyping, onIdle, delay]
  );

  const clear = useCallback(() => {
    if (timeoutRef.current) {
      window.clearTimeout(timeoutRef.current);
      timeoutRef.current = null;
    }
  }, []);

  return { handleEdit, clear };
}
