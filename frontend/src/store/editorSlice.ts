import { createSlice, PayloadAction } from "@reduxjs/toolkit";
import { User } from "../types";

interface EditorState {
  code: string;
  username: string | null;
  roomId: string | null;
  users: User[];
  suggestion: string;
  typingUsers: string[]; // list of usernames typing
  roomLimit: number | null; // NEW: track room limit
}

const initialState: EditorState = {
  code: "# Start coding...",
  username: null,
  roomId: null,
  users: [],
  suggestion: "",
  typingUsers: [],
  roomLimit: null,
};

const editorSlice = createSlice({
  name: "editor",
  initialState,
  reducers: {
    setUsername(state, action: PayloadAction<string | null>) {
      state.username = action.payload;
    },
    setRoomId(state, action: PayloadAction<string | null>) {
      state.roomId = action.payload;
    },
    setCode(state, action: PayloadAction<string>) {
      state.code = action.payload;
    },
    setUsers(
      state,
      action: PayloadAction<{ users: User[]; limit?: number | null }>
    ) {
      const { users, limit } = action.payload;
      state.users = users;
      state.typingUsers = users.filter((u) => u.typing).map((u) => u.username);
      if (limit !== undefined) state.roomLimit = limit; // update limit
    },
    setSuggestion(state, action: PayloadAction<string>) {
      state.suggestion = action.payload;
    },
    setTypingUsers(state, action: PayloadAction<string[]>) {
      state.typingUsers = action.payload;
    },
    setRoomLimit(state, action: PayloadAction<number | null>) {
      state.roomLimit = action.payload;
    },
    resetAll(state) {
      state.code = "# Start coding...";
      state.username = null;
      state.roomId = null;
      state.users = [];
      state.suggestion = "";
      state.typingUsers = [];
      state.roomLimit = null;
    },
  },
});

export const {
  setUsername,
  setRoomId,
  setCode,
  setUsers,
  setSuggestion,
  setTypingUsers,
  setRoomLimit,
  resetAll,
} = editorSlice.actions;

export default editorSlice.reducer;
