// src/hooks/useWebSocket.ts
import { useEffect, useRef, useCallback } from "react";
import { WsMessage } from "../types";

const BACKEND_WS_BASE =
  process.env.REACT_APP_BACKEND_HTTP || "ws://localhost:8000";

export function useWebSocket(
  roomId: string | null,
  username: string | null,
  handlers: {
    onCode?: (code: string) => void;
    onUsers?: (users: any[]) => void;
    onTyping?: (typingUsers: string[]) => void;
  } = {}
) {
  const wsRef = useRef<WebSocket | null>(null);

  const handlerRef = useRef(handlers);
  handlerRef.current = handlers;

  useEffect(() => {
    if (!roomId || !username) return;

    const url = `${BACKEND_WS_BASE}/ws/${roomId}/${username}`;
    const ws = new WebSocket(url);
    wsRef.current = ws;

    const handleMessage = (ev: MessageEvent) => {
      try {
        const msg: WsMessage = JSON.parse(ev.data);

        const { onCode, onUsers, onTyping } = handlerRef.current;

        switch (msg.type) {
          case "CODE_UPDATE":
            onCode?.(msg.code);
            break;
          case "USER_UPDATE":
            onUsers?.(msg.users);
            break;
          case "TYPING_UPDATE":
            onTyping?.(msg.typingUsers);
            break;
        }
      } catch (err) {
        if (process.env.NODE_ENV === "development") {
          console.error("ws parse error", err);
        }
      }
    };

    ws.addEventListener("message", handleMessage);

    return () => {
      ws.removeEventListener("message", handleMessage);
      try {
        ws.close();
      } catch {}
      wsRef.current = null;
    };
  }, [roomId, username]);

  const send = useCallback((payload: object) => {
    const socket = wsRef.current;
    if (socket && socket.readyState === WebSocket.OPEN) {
      socket.send(JSON.stringify(payload));
    }
  }, []);

  const sendCode = useCallback(
    (code: string) => send({ type: "CODE_UPDATE", code }),
    [send]
  );

  const sendTyping = useCallback(
    (typing: boolean) => send({ type: "TYPING_UPDATE", typing }),
    [send]
  );

  const close = useCallback(() => {
    if (wsRef.current) {
      try {
        wsRef.current.close();
      } catch {}
      wsRef.current = null;
    }
  }, []);

  return { sendCode, sendTyping, close };
}
