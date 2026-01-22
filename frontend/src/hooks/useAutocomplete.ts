import { useRef, useCallback, useEffect, useMemo } from "react";
import debounce from "lodash.debounce";

const BACKEND_HTTP_BASE = process.env.REACT_APP_BACKEND_HTTP;

export function useAutocomplete() {
  const suggestionsRef = useRef<string[]>([]);
  const monacoRef = useRef<any | null>(null);
  
  const providerDisposableRef = useRef<any>(null);

// Wrap the logic in useCallback to make it stable
  const fetchSuggestionsInner = useCallback(async (word: string) => {
    if (!word) {
      suggestionsRef.current = [];
      return;
    }

    try {
      const res = await fetch(`${BACKEND_HTTP_BASE}/autocomplete/`, {
        method: "POST",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          code: word,
          cursorPosition: word.length,
          language: "python",
        }),
      });

      const data = await res.json();
      suggestionsRef.current = data?.suggestion ? [data.suggestion] : [];

      // Force suggest popup if monaco is present
      const editor = monacoRef.current?.editorInstance;
      if (suggestionsRef.current.length > 0) {
        editor?.getAction?.("editor.action.triggerSuggest")?.run?.();
      }
    } catch (err) {
      suggestionsRef.current = [];
      if (process.env.REACT_APP_BACKEND_HTTP) console.error("autocomplete error", err);
    }
  }, []); // Dependencies are empty because refs are stable
  const fetchSuggestions = useMemo(
    () => debounce(fetchSuggestionsInner, 400),
    [fetchSuggestionsInner] 
  );

  const init = useCallback((monaco: any, editorInstance: any) => {
    monacoRef.current = { monaco, editorInstance };


    if (providerDisposableRef.current) {
      providerDisposableRef.current.dispose();
    }

    providerDisposableRef.current = monaco.languages.registerCompletionItemProvider("python", {
      triggerCharacters: ["_", ".", " "],
      provideCompletionItems: (model: any, position: any) => {
        const suggestions = [...suggestionsRef.current];

        const wordInfo = model.getWordAtPosition(position) || {
          word: "",
          startColumn: position.column,
          endColumn: position.column,
        };

        const range = new monaco.Range(
          position.lineNumber,
          wordInfo.startColumn,
          position.lineNumber,
          wordInfo.endColumn
        );

        return {
          suggestions: suggestions.map((s: string) => ({
            label: s,
            kind: monaco.languages.CompletionItemKind.Text,
            insertText: s,
            range,
          })),
        };
      },
    });
  }, []);

  useEffect(() => {
    return () => {
      if (providerDisposableRef.current) {
        providerDisposableRef.current.dispose();
      }
    };
  }, []);

  return { init, fetchSuggestions, suggestionsRef };
}