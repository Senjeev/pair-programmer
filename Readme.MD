
# PAIR--PROGRAMMING WEB APPLICATION
 
Build a simplified real-time pair-programming web application. Multiple users should be able to join the same room, edit code at the same time, and see each other’s changes instantly. The system also provide an AI-style autocomplete suggestions.

## Demo

Link to demo

https://pair-programmer-lake.vercel.app/

### UI Preview: Landing Page

Below is a screenshot of the application's landing page where users can join or create a collaborative room.

![Pair Programming](/frontend/public/front-page.png)

## Tech Stack

**Frontend:** React, TypeScript, Redux Toolkit

 **Backend:** Python, FastAPI, WebSockets


## Environment Variables

To run this project, you will need to add the following environment variables to your .env file

```bash
 cd backend
```
create a .env and paste  below one with you actual DB URI

```bash
`DATABASE_URL`: postgresql://username:password@localhost:5432/realtime
```

```bash
 cd backend
```
create a .env and paste  below one

```bash
REACT_APP_BACKEND_HTTP=http://localhost:8000
```


## Run Locally

Clone the project

## Backend
```bash
 cd backend
```
Install the required dependencies in virtual environment

```bash
 python3 -m venv venv

 source venv/bin/activate

 venv\Scripts\activate

 pip install -r requirements.txt
```
After that run the below command
```bash
 uvicorn app.main:app –reload                         (Server will be on live)
```
## Frontend

```bash
 cd frontend        

 npm install 

 npm start                
```
## Project Structure
```
backend/
│── app/
│   ├── main.py
│   ├── database.py
│   ├── manager.py
│   ├── models.py
│   ├── schemas.py
│   ├── services/
│   │     └── roomServices.py
│   ├── routers/
│   │     ├── rooms.py
│   │     ├── autocomplete.py
│   │     └── websockets.py
│   └── constants.py
│── requirements.txt
│── README.md  
```

## 3. Architecture Overview
* FastAPI Backend
    - Provides REST APIs for room creation(Unique id for each room) and autocomplete.
    - Provides WebSocket endpoints for real-time communication.
* Postgres
   - Stores room state (users, last saved code).
   - Stores room id (unique),list of users, lastly  saved code user name, room limit
* WebSocket
    - Tracks active connections.
    - Broadcasts code updates across users in a room.
    - Manages typing indicators and user presence.
### 3.1. WebSocket ↔ DB Sync Logic

| Action | In-Memory | Database |
| :--- | :--- | :--- |
| **User types** | Code stored in manager | Not saved instantly |
| **User disconnects** | Manager removes user | Saves code & marks user offline |
| **New user joins** | Latest in-memory code is served | Falls back to DB if needed |

This ensures:
   - Ultra-fast collaboration
   - DB persistence on disconnect
   - Consistency even after server restart


## 4. Design Choices

### 1.1. Backend Framework
* **Choice:** FastAPI
* High performance asynchronous support (important for WebSockets and real-time updates).
* Easy integration with dependency injection (e.g., database sessions via `Depends(get_db)`).

### 1.2. Database
* **Choice:** PostgreSQL (SQLAlchemy ORM) with JSON fields for dynamic user lists (`MutableList.as_mutable(JSON)`).
* Persistent storage of room information (**Room table**) ensures users and code are not lost if the server restarts.
* JSON columns allow flexible storage of users and their online status.
* Using **SQLAlchemy** with `SessionLocal` provides transaction management and automatic rollback in case of errors.

### 1.3. WebSocket Design
* Real-time communication using WebSockets allows immediate sync of code edits between users.
* **Manager maintains:**
    * Active connections per room.
    * Typing status per user.
    * In-memory latest code for faster initial load when a new user joins.
    * Locks (`asyncio.Lock`) per room ensure thread-safe updates of active connections and code broadcast.

### 1.4. Code Syncing & In-Memory Storage
* Reduces unnecessary database reads.
* Ensures that a newly connected user receives the most recent code instantly using in-memory code for the current room.

### 1.5. Room Management Endpoints
* `POST /rooms` → Create room.
* `GET /rooms/{room_id}` → Join room, mark users online, send current code in the editor.
* `PATCH /rooms/{room_id}/limit` → Adjust room limits dynamically.
* `POST /rooms/save` → Save code to DB.

### 1.6. Autocomplete Design
* Static, rule-based suggestion system using: `PYTHON_KEYWORDS`, `PYTHON_BUILTINS`, `PYTHON_METHODS`, `PYTHON_MODULES`.
* Uses regex matching for prefix-based suggestions.

### 1.7. Service Layer
* Centralizes user and room-related logic (e.g., marking offline, sending user list).
* Promotes separation of concerns: WebSocket endpoint only handles communication, while services and managers handle DB operations and business logic.


## 6. Endpoints

### Room Creation
* **Method:** `POST`
* **URL:** `http://localhost:8000/rooms?username=John&roomId=room1223&limit=5`

### Join Existing Room
* **Method:** `GET`
* **URL:** `http://localhost:8000/rooms/Senjeev-room-A4KG08?username=Senjeev`

### Autocomplete
* **Method:** `POST`
* **URL:** `http://localhost:8000/autocomplete`
* **Payload:**
  ```json
  {
    "code": "de",
    "cursorPosition": 2,
    "language": "python"
  }


## 7. LIMITATIONS:

| Area | Current Behaviour | Limitation / Why |
| :--- | :--- | :--- |
| Real-Time Sync | WebSocket broadcasts code to all users; typing indicator implemented | **No live cursors:** cannot see exact cursor positions of other users |
| Persistence | Single table stores room code and users | **Scalability issue:** difficult to track data if multiple customers/rooms grow; no table-level separation |
| Code History | Only latest code snapshot is saved on disconnect | **No detailed log/history:** cannot track edits per user or recover intermediate changes |
| Frontend Metadata | Whole code is saved per update | Cannot track **“last edited by”**: edits from multiple users overwrite the previous state |
| Authentication | Username passed via URL | **No login/JWT/Auth:** vulnerable to spoofing |
| Scaling | Single-instance in-memory manager | **Cannot horizontally scale:** needs Redis or similar for multi-instance support |
| Autocomplete | Regex-based word suggestions | **Not AI-powered:** lacks context-aware suggestions |
| IDE/Editor | Simple text editor assigned (Monaco) | **No programming IDE features:** lacks syntax highlighting, language support, linting, and code formatting |



## 8. Improvements With More Time

### 1. Secure Authentication & Authorization
* **Add JWT login and role-based access:**
    * **Admin:** Manage rooms, users.
    * **User:** Edit/join rooms.
* Prevents URL spoofing and unauthorized edits.

### 2. Cursor-Level Collaboration & Editor Improvements
* Extend current typing indicator to **live cursors** per user.
* Highlight who is typing where in the code editor.
* Improvise the current **Monaco Editor** or replace it with **CodeMirror** / **ACE Editor**.
* **Features:**
    * Syntax highlighting for multiple languages.
    * Code linting and formatting.
    * Auto-completion with AI or language server support.

### 3. DB Architecture & Multi-Tenant Support
* Split single table into multiple tables or schemas per customer/room.
* Use relational links between users, rooms, and code history for better tracking.
* Easier to manage large-scale data and maintain audit logs.
* Periodic background saves to DB to prevent data loss.
* Integrate with code history and multi-user edits.

### 4. Advanced Autocomplete
* Replace current API with context-aware, **AI-driven suggestions**.
* Supports multiple programming languages and smart code snippets.

### 5. Multi-Instance Real-Time Sync
* Introduce **Redis Pub/Sub** or similar for cross-instance communication.
* Support horizontal scaling for more users/rooms.

## 9. Frontend Features

### 9.1. Room Creation Flow
* Users can create a room only after entering a valid username.
* **Username validation rules:**
    * Must not be empty.
    * Must be at least 3 characters long.
* If the username is missing or too short → Room creation is blocked with a proper UI message.
* While creating a room, the user must enter the **initial room limit**.
* **Maximum allowed room limit:** 20 users.
* Limit is validated before room creation; invalid limits are rejected with a UI alert.

### 9.2. Room Join Functionality
* Users can join an existing room using:
    * Room ID
    * Username
* If the room is **not full**, the user is allowed in; otherwise, the UI shows a *"Room is full"* message.
* **Username Collision Handling:**
    * If a user with the same username is already present & online:
        * Another user cannot join using the same username.
        * UI shows: `"Username already exists"`.

### 9.3. Code Editor UI
* The **Room ID** is displayed on the editor’s top-right corner (facilitating easy sharing).
* **Typing indication** is implemented to show when a user is typing to others.
* **User List:** Displays connected users (distinguishes online vs. offline using color differentiation).
* **Stats Panel:** Shows total online users, total users, and the room limit.
* **Controls:**
    * **Save Button:** Sends the current code content to the backend.
    * **Limit Button:** Allows editing the limit with backend validation (new limit must be greater than the current one).
    * **Disconnect Button:** Allows the user to immediately exit:
        1. WebSocket connection closes.
        2. User is marked offline to other online users.
