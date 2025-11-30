// src/components/CodeEditor.tsx
import React, { useEffect, useRef, useState, useCallback } from "react";
import Editor, { OnMount } from "@monaco-editor/react";
import { useSelector, useDispatch } from "react-redux";
import { RootState } from "../store/store";
import { setCode, setUsers, resetAll, setRoomLimit } from "../store/editorSlice";
import { useWebSocket } from "../hooks/useWebSocket";
import { useAutocomplete } from "../hooks/useAutocomplete";
import { useDebouncedTyping } from "../hooks/useDebouncedTyping";
import ConfirmModal from "./ConfirmModal";
import "../App.css";
import ModalInput from "./ModalInput";

const CodeEditor: React.FC = () => {
  const dispatch = useDispatch();
  const { roomId, username, users, code ,roomLimit} = useSelector(
    (s: RootState) => s.editor
  );
  const [editLimitOpen, setEditLimitOpen] = useState(false);

  const editorRef = useRef<any | null>(null);
  const monacoRef = useRef<any | null>(null);
  const [saveConfirmOpen, setSaveConfirmOpen] = useState(false);
  // Popup state
  const [popup, setPopup] = useState<{
    type: "success" | "error" | "info";
    message: string;
  } | null>(null);

  const showPopup = (type: any, message: string) => {
    setPopup({ type, message });
    setTimeout(() => setPopup(null), 2300);
  };

  // confirm disconnect modal
  const [confirmOpen, setConfirmOpen] = useState(false);

  // websocket handlers update redux
  const { sendCode, sendTyping, close } = useWebSocket(roomId, username, {
    onCode: (newCode) => dispatch(setCode(newCode)),
    onUsers: (newUsers) =>dispatch(setUsers({ users: newUsers, limit: roomLimit})) 

  });

  const { init: initAutocomplete, fetchSuggestions } = useAutocomplete();

  const { handleEdit, clear } = useDebouncedTyping(
    (isTyping) => sendTyping(isTyping),
    (editorInstance) => {
      try {
        const pos = editorInstance.getPosition();
        const model = editorInstance.getModel();
        if (!pos || !model) return;
        const wordInfo = model.getWordUntilPosition(pos);
        const currentWord = wordInfo?.word || "";
        fetchSuggestions(currentWord);
      } catch (err) {
        console.error(err);
      }
    },
    400
  );

  const handleEditorMount: OnMount = (editor, monaco) => {
    editorRef.current = editor;
    monacoRef.current = monaco;
    initAutocomplete(monaco, editor);
  };

  const onEdit = useCallback(
    (value: string | undefined) => {
      const text = value ?? "";
      dispatch(setCode(text));
      sendCode(text);

      if (editorRef.current) handleEdit(editorRef.current);
    },
    [dispatch, sendCode, handleEdit]
  );

  // API: Save Room Name
 const saveCode = async () => {
  if (!roomId || !username) return showPopup("error", "Missing room or username.");
  try {
    const res = await fetch(`${process.env.REACT_APP_BACKEND_HTTP}/rooms/save`, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({
        roomId,
        username,
        code
      }),
    });

    // Handle based on Status Code
    if (res.status === 200) {
      showPopup("success", "Code saved successfully!");
    } 
    else if (res.status === 304) {
      showPopup("info", "No changes — Code is the same.");
    } 
    else if (res.status === 404) {
      showPopup("error", "Room not found.");
    } 
    else {
      showPopup("error", "Unexpected server error.");
    }
  } catch (err) {
    showPopup("error", "Network / server error.");
  }
};
//edit Limit per room
const handleEditLimitSubmit = async (value: string) => {
  setEditLimitOpen(false);
  const newLimit = parseInt(value);
  if (isNaN(newLimit) || newLimit < 1 || newLimit > 20) {
    return showPopup("error", "Limit must be 1-20");
  }

  try {
    const res = await fetch(`${process.env.REACT_APP_BACKEND_HTTP}/rooms/${roomId}/limit?new_limit=${newLimit}`, {
      method: "PATCH",
    });

    if (!res.ok) {
      const data = await res.json();
      return showPopup("error", data.detail || "Failed to update limit");
    }

    showPopup("success", `Room limit updated to ${newLimit}`);
    dispatch(setRoomLimit(newLimit));
  } catch (err) {
    showPopup("error", "Server error");
  }
};


  useEffect(() => {
    return () => {
      clear();
      sendTyping(false);
      close();
    };
  }, [clear, close, sendTyping]);

  if (!roomId)
    return (
      <div className="code-editor-container card">
        <p className="empty-state">Join a room to start coding</p>
      </div>
    );

  const onlineCount = users.filter((u) => u.online).length;

  return (
    <>
      {/* POPUP */}
      {popup && (
        <div className="popup-container">
          <div className={`popup popup-${popup.type}`}>
            <span>{popup.message}</span>
            <button className="popup-close" onClick={() => setPopup(null)}>
              ×
            </button>
          </div>
        </div>
      )}

      <div className="code-editor-container card">
        <div className="editor-header">
          {/* Left */}
          <div className="header-left">
            <h2 className="editor-title">Editor</h2>
            <div className="connection-status">
              <span className={`status-dot ${roomId ? "connected" : ""}`} />
              {roomId ? "Connected" : "Offline"}
            </div>
          </div>

          {/* SAVE BUTTON */}
          <div className="room-info" style={{ gap: "8px" }}>
            <button className="btn btn-primary" onClick={() => setSaveConfirmOpen(true)} style={{ padding: "8px 14px" }}> 
              Save
            </button>

            <button className="btn btn-secondary-limit" onClick={() => setEditLimitOpen(true)} style={{ padding: "8px 14px" }}>
              Limit
            </button>
            <span className="room-badge">Room ID: {roomId}</span>

            <button
              className="btn btn-secondary"
              onClick={() => setConfirmOpen(true)}
              aria-label="Disconnect"
            >
              Disconnect
            </button>
          </div>
        </div>

        {/* USERS LIST */}
        <div className="users-section">
          <div className="users-header">
            <strong>Users</strong>
            <span className="users-count">
              Total: {users.length} | Online: {onlineCount} | Limit: {roomLimit ?? "-"}
            </span>
          </div>

          <div className="users-list">
            {users.map((u, idx) => (
              <div
                className={`user-badge ${u.online ? "online" : "offline"}`}
                key={u.username + idx}
                title={`${u.username}${u.typing ? " (typing)" : ""}`}
              >
                <span className="badge-avatar">
                  {u.username?.[0]?.toUpperCase()}
                </span>
                {u.username} {u.typing && "✍️"}
              </div>
            ))}
          </div>
        </div>

        {/* MONACO EDITOR */}
        <div className="editor-wrapper">
          <Editor
            height="70vh"
            defaultLanguage="python"
            value={code}
            theme="vs-dark"
            onChange={onEdit}
            onMount={handleEditorMount}
            options={{
              minimap: { enabled: false },
              tabSize: 2,
              insertSpaces: true,
            }}
          />
        </div>

        {/* Confirm Disconnect */}
        {confirmOpen && (
          <ConfirmModal
            title="Disconnect?"
            message={`Are you sure you want to disconnect from room "${roomId}"?`}
            onConfirm={async() => {
              await saveCode();
              dispatch(resetAll());
              setConfirmOpen(false);
            }}
            onCancel={() => setConfirmOpen(false)}
          />
        )}
        {saveConfirmOpen && (
          <ConfirmModal
          title="Save Code?"
          message="Are you sure you want to save the current code?"
          onConfirm={() => {
        saveCode();
        setSaveConfirmOpen(false);
        }}
        onCancel={() => setSaveConfirmOpen(false)}/>
        )}
        {editLimitOpen && (
        <ModalInput
          title="Edit Room Limit"
          placeholder="Enter new limit (1-20)"
          onSubmit={handleEditLimitSubmit}
          onClose={() => setEditLimitOpen(false)}
        />
        )}

      </div>
    </>
  );
};

export default React.memo(CodeEditor);
