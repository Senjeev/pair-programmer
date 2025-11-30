// shared types used across the app
export interface User {
  id?: string;
  username: string;
  typing?: boolean;
  online?: boolean;
}

export interface WsMessage {
  type: string;
  [k: string]: any;
}
