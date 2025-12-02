// src/App.tsx
import React, { useState, useRef, useEffect } from "react";
import { Provider, useDispatch, useSelector } from "react-redux";
import { store, RootState } from "./store/store";
import { setRoomId, setRoomLimit, setUsername } from "./store/editorSlice";
import CodeEditor from "./components/CodeEditor";
import { BrowserRouter as Router, useLocation, useNavigate } from "react-router-dom";
import Popup from "./components/Popup";
import ModalInput from "./components/ModalInput";
import "./App.css";
import BackgroundRays from "./components/BackgroundRays";

// Helper to generate Room ID using trimmed username
const generateRoomId = (username: string) => {
  const safeUser = username.trim();
  const random = Math.random().toString(36).substring(2, 8).toUpperCase();
  return `${safeUser}-room-${random}`;
};

interface RoomManagerProps {
  addPopup: (message: string, type?: "success" | "error" | "info") => void;
}

const RoomManager: React.FC<RoomManagerProps> = ({ addPopup }) => {
  const dispatch = useDispatch();
  const [enteredUsername, setEnteredUsername] = useState("");
  const [roomModalOpen, setRoomModalOpen] = useState(false);
  const [limitModalOpen, setLimitModalOpen] = useState(false);

  const roomId = useSelector((s: RootState) => s.editor.roomId);

  const alreadyConnected = () => {
    if (roomId) {
      addPopup("You are already in a room. Disconnect first.", "error");
      return true;
    }
    return false;
  };

  // Step 1: Ask username & then room limit
  const createRoom = async () => {
    if (alreadyConnected()) return;

    // TRIM HERE
    const trimmedUsername = enteredUsername.trim();

    if (!trimmedUsername) return addPopup("Enter username", "error");
    if (trimmedUsername.length < 3) return addPopup("Username should have atleast 3 characters", "error");

    // Open modal to ask for room limit
    setLimitModalOpen(true);
  };

  const handleLimitSubmit = async (limitInput: string) => {
    setLimitModalOpen(false);
    
    // TRIM HERE
    const trimmedUsername = enteredUsername.trim();

    const limit = parseInt(limitInput);
    if (isNaN(limit) || limit < 1 || limit > 10) {
      return addPopup("Room limit must be 1-10", "error");
    }

    // Use trimmed username for generation
    const newRoomId = generateRoomId(trimmedUsername);

    try {
      // Use trimmedUsername in API call
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_HTTP}/rooms?username=${trimmedUsername}&roomId=${newRoomId}&limit=${limit}`,
        { method: "POST" }
      );

      if (!res.ok) {
        addPopup("Server error", "error");
        return;
      }

      // Store trimmed values in Redux
      dispatch(setUsername(trimmedUsername));
      dispatch(setRoomId(newRoomId));
      addPopup(`Room created!`, "success");
      dispatch(setRoomLimit(limit));

    } catch (err) {
      console.log(err);
      addPopup("Server error", "error");
    }
  };

  const joinRoom = async () => {
    if (alreadyConnected()) return;
    
    // TRIM HERE
    const trimmedUsername = enteredUsername.trim();

    if (!trimmedUsername) return addPopup("Enter username", "error");
    if (trimmedUsername.length < 3) return addPopup("Username should have atleast 3 characters", "error");
    
    setRoomModalOpen(true);
  };

  const handleRoomSubmit = async (roomIdInput: string) => {
    setRoomModalOpen(false);

    // TRIM BOTH INPUTS HERE
    const trimmedRoomId = roomIdInput.trim();
    const trimmedUsername = enteredUsername.trim();

    if (!trimmedRoomId) return addPopup("Room ID required", "error");

    try {
      // Use trimmed values in API call
      const res = await fetch(
        `${process.env.REACT_APP_BACKEND_HTTP}/rooms/${trimmedRoomId}?username=${trimmedUsername}`
      );

      if (res.status === 409) return addPopup("User with this name already exists", "error");
      if (res.status === 404) return addPopup("Room not found", "error");
      if (res.status === 403) return addPopup("Room is full", "error");
      if (!res.ok) return addPopup("Server error", "error");

      const data = await res.json();
      
      // Store trimmed values in Redux
      dispatch(setRoomId(trimmedRoomId));
      dispatch(setUsername(trimmedUsername));
      dispatch(setRoomLimit(data.limit));
      addPopup("Joined room successfully!", "success");
    } catch {
      addPopup("Server error", "error");
    }
  };

  return (
    <div className="room-manager-wrapper">
      <div className="room-manager card">
        <h2>Join or Create Room</h2>

        <label className="label">Your Username</label>
        <input
          className="input"
          placeholder="Enter username..."
          value={enteredUsername}
          onChange={(e) => setEnteredUsername(e.target.value)}
        />

        <div className="room-actions">
          <button className="btn btn-primary" onClick={createRoom}>
            Create Room
          </button>
          <button className="btn btn-secondary" onClick={joinRoom}>
            Join Room
          </button>
        </div>
      </div>

      {/* Modal for entering room ID */}
      {roomModalOpen && (
        <ModalInput
          title="Enter Room ID"
          placeholder="Room ID..."
          onSubmit={handleRoomSubmit}
          onClose={() => setRoomModalOpen(false)}
        />
      )}

      {/* Modal for entering room limit */}
      {limitModalOpen && (
        <ModalInput
          title="Set Room Limit"
          placeholder="Max users (1-10)"
          onSubmit={handleLimitSubmit}
          onClose={() => setLimitModalOpen(false)}
        />
      )}
    </div>
  );
};


const RoomUrlHandler: React.FC<{ addPopup: (m: string, t?: any) => void }> = ({ addPopup }) => {
  const { pathname, search } = useLocation();
  const navigate = useNavigate();
  const dispatch = useDispatch();
  const hasRun = useRef(false);

  const [usernameModalOpen, setUsernameModalOpen] = useState(false);
  const [pendingRoomId, setPendingRoomId] = useState<string | null>(null);

  useEffect(() => {
    if (hasRun.current) return;
    hasRun.current = true;

    // Match /rooms/<id>
    const match = pathname.match(/\/rooms\/([^\/\?]+)/);
    if (!match) return;

    // Trim roomId from URL
    const roomId = match[1].trim();
    setPendingRoomId(roomId);

    // Read username from query
    const query = new URLSearchParams(search);
    const rawUsername = query.get("username");

    if (rawUsername) {
      // Trim username from URL parameters
      const trimmedUsername = rawUsername.trim();
      handleAutoJoin(roomId, trimmedUsername);
    } else {
      // Ask for username
      setUsernameModalOpen(true);
    }
  }, [pathname, search]);

  const handleAutoJoin = async (roomId: string, username: string) => {
    // Ensure inputs are trimmed just in case
    const safeRoomId = roomId.trim();
    const safeUsername = username.trim();

    try {
      const res = await fetch(`${process.env.REACT_APP_BACKEND_HTTP}/rooms/${safeRoomId}?username=${safeUsername}`);

      if (!res.ok) {
        addPopup("Room not found or full", "error");
        return navigate("/");
      }

      const data = await res.json();
      dispatch(setUsername(safeUsername));
      dispatch(setRoomId(safeRoomId));
      dispatch(setRoomLimit(data.limit));
      addPopup("Joined via URL!", "success");
    } catch {
      addPopup("Server error", "error");
      navigate("/");
    }
  };

  const handleUsernameSubmit = async (userInput: string) => {
    setUsernameModalOpen(false);
    
    // TRIM HERE
    const trimmedInput = userInput.trim();

    if (!trimmedInput) {
      addPopup("Username required", "error");
      return navigate("/");
    }

    if (!pendingRoomId) return;

    handleAutoJoin(pendingRoomId, trimmedInput);
  };

  return (
    <>
      {usernameModalOpen && (
        <ModalInput
          title="Enter your username"
          placeholder="Username..."
          onSubmit={handleUsernameSubmit}
          onClose={() => setUsernameModalOpen(false)}
        />
      )}
    </>
  );
};


export default function App() {
  const [popups, setPopups] = useState<
    { id: number; message: string; type: "success" | "error" | "info" }[]
  >([]);

  const addPopup = (message: string, type: "success" | "error" | "info" = "info") => {
    const id = Date.now();
    setPopups((prev) => [...prev, { id, message, type }]);
    setTimeout(() => setPopups((prev) => prev.filter((p) => p.id !== id)), 3000);
  };

  return (
    <Provider store={store}>
      <Router>
        <BackgroundRays />

        <div className="popup-container">
          {popups.map((p) => (
            <Popup
              key={p.id}
              message={p.message}
              type={p.type}
              onClose={() => setPopups((prev) => prev.filter((popup) => popup.id !== p.id))}
            />
          ))}
        </div>

        <div className="App">
          <header className="app-header">
            <h1 className="app-title">PAIR - PROGRAMMING</h1>
            <p className="app-subtitle">Real-time collaborative coding</p>
          </header>

          <main className="app-main">
            <RoomUrlHandler addPopup={addPopup} />
            <RoomManager addPopup={addPopup} />
            <CodeEditor />
          </main>
        </div>
      </Router>
    </Provider>
  );
}