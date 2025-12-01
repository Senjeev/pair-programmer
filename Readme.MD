                                    PAIR--PROGRAMMING WEB APPLICATION

OVERVIEW:
       Build a simplified real-time pair-programming web application. Two users should be able to join the same room, edit code at the same time, and see each other’s changes instantly. The system also provide an AI-style autocomplete suggestion.

TECH STACK USED:
Backend                       : Python, FastAPI, WebSockets
Frontend                      : React, TypeScript, Redux Toolkit
Tools Used                    : VS Code,PostMan,Postgresql(pgAdmin4)
Deployment                    : Backend -   RENDER website, Front end – VERCEL website



1. PROJECT STRUCTURE:
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

2. HOW TO RUN THE PROJECT:
•	Clone the Repo: https://github.com/Senjeev/pair-programmer
Backend
•	Cd backend
•	python3 -m venv venv
•	source venv/bin/activate  
•	venv\Scripts\activate
•	pip install -r requirements.txt
•	Create a .env file and add 
DATABASE_URL=postgresql://username:password@localhost:5432/realtime.
•	Run Fast Api uvicorn app.main:app –reload (Server will be on live)
Front end 
•	Cd front end 
•	npm install 
•	npm start (UI will be launched)


3. Architecture Overview
🔹 FastAPI Backend
•	Provides REST APIs for room creation(Unique id for each room) and autocomplete.
•	Provides WebSocket endpoints for real-time communication.
🔹 Postgres
•	Stores room state (users, last saved code).
•	Stores room id (unique),list of users, lastly  saved code user name, room limit
🔹 WebSocket
•	Tracks active connections.
•	Broadcasts code updates across users in a room.
•	Manages typing indicators and user presence.

3.1. WebSocket ↔ DB Sync Logic
Action	In-Memory	Database
User types	Code stored in manager	Not saved instantly
User disconnects	Manager removes user	Saves code & marks user offline
New user joins	Latest in-memory code is served	Falls back to DB if needed

This ensures:
1.	Ultra-fast collaboration
2.	DB persistence on disconnect
3.	Consistency even after server restart


4. DESIGN CHOICES
1.1. BACKEND FRAMEWORK
•	Choice: FastAPI
•	High performance asynchronous support (important for WebSockets and real-time updates).
•	Easy integration with dependency injection (e.g., database sessions via Depends(get_db)).
1.2	  DATABASE
•	Choice: PostgreSQL (SQLAlchemy ORM) with JSON fields for dynamic user lists (MutableList.as_mutable(JSON)).
•	Persistent storage of room information (Room table) ensures users and code are not lost if server restarts.
•	JSON columns allow flexible storage of users and their online status.
•	Using SQLAlchemy with SessionLocal provides transaction management and automatic rollback in case of errors.

1.3	 WEBSOCKET DESIGN
•	Real-time communication using WebSockets allows immediate sync of code edits between users.
Manager maintains:
•	Active connections per room.
•	Typing status per user.
•	In-memory latest code for faster initial load when a new user joins.
•	Locks (asyncio.Lock) per room ensure thread-safe updates of active connections and code broadcast.
1.4. CODE SYNCING & IN-MEMORY STORAGE
•	Reduces unnecessary database reads.
•	Ensures that a newly connected user receives the most recent code instantly using in memory code for the current room.
1.5. ROOM MANAGEMENT
ENDPOINTS:
•	POST /rooms → create room.
•	GET /rooms/{room_id} → join room, mark users online, sending current code in the editor.
•	PATCH /rooms/{room_id}/limit → adjust room limits dynamically.
•	POST /rooms/save → save code to DB.
1.6. AUTOCOMPLETE DESIGN
•	Static, rule-based suggestion system using: PYTHON_KEYWORDS, PYTHON_BUILTINS, PYTHON_METHODS, PYTHON_MODULES.
•	Uses regex matching for prefix-based suggestions.
1.7. SERVICE LAYER
•	Centralizes user and room-related logic (e.g., marking offline, sending user list).
•	Promotes separation of concerns: WebSocket endpoint only handles communication, while services ,managers handle DB operations and business logic.

6. ENDPOINTS:
•	Rooms Creation - POST
http://localhost:8000/rooms?username=John&roomId=room1223&limit=5
•	Existing Room   - GET
 http://localhost:8000/rooms/Senjeev-room-A4KG08?username=Senjeev
•	Autocomplete    - POST
http://localhost:8000/autocomplete
Payload: {"code": "de","cursorPosition": 2,  "language":"python" }
•	Save code          - POST
http://localhost:8000/rooms/save
Payload :{ "roomId": "your_room_id",
                "code": "your_code_here",
               "username": "your_username"
		}
•	Update Limit     - PATCH
http://localhost:8000/rooms/senjeev-393u/limit?new_limit=5
•	WebSocket 
wss://localhost:8000/ws/room123/Senjeev

7. LIMITATIONS:

1.1. Real-Time Sync

Current Behaviour: WebSocket broadcasts code to all connected users; typing indicator works.

Limitation: No real-time cursor sharing. Users cannot see each other's exact cursor positions.

1.2. Persistence Layer

Current Behaviour: A single database table stores room code and user details.

Limitation: Not scalable. As the number of customers/rooms increases, it becomes difficult to manage and isolate data without table-level separation.

1.3. Code History & Versioning

Current Behaviour: Only the latest code snapshot is saved when a user disconnects.

Limitation: No detailed version history. Cannot track step-by-step changes or recover intermediate edits.

1.4. Frontend Metadata Tracking

Current Behaviour: Entire code is saved during each update.

Limitation: No "last edited by" tracking. When multiple users edit, every save overwrites the previous editor metadata.

1.5. Authentication

Current Behaviour: Username is passed through URL or frontend state during join.

Limitation: No authentication system (JWT/login). Easy to impersonate users; no identity verification.

1.6. Horizontal Scaling

Current Behaviour: Uses an in-memory connection manager (single process).

Limitation: Cannot scale across multiple backend instances. Requires Redis Pub/Sub or other distributed message system.

1.7. Autocomplete

Current Behaviour: Simple regex-based autocomplete that suggests words from existing code.

Limitation: Not context-aware or intelligent. Lacks true AI completion logic.

1.8. IDE / Editor Capabilities

Current Behaviour: Monaco editor is used as a plain text editor.

Limitation: Missing real IDE features such as:

Syntax highlighting per language

Language server support (Python/Java/JS)

Linting

Code formatting

Error markers




8. IMPROVEMENTS WITH MORE TIME 

1. SECURE AUTHENTICATION & AUTHORIZATION:
•	Add JWT login and role-based access:
o	Admin: manage rooms, users
o	User: edit/join rooms
•	Prevents URL spoofing and unauthorized edits.
2. CURSOR-LEVEL COLLABORATION AND CODE EDITOR IMPROVEMENTS:
•	Extend current typing indicator to live cursors per user.
•	Highlight who is typing where in the code editor.
•	Improvise the current Monaco Editor or replace it with / Code Mirror / ACE Editor.
•	Features:
o	Syntax highlighting for multiple languages
o	Code linting and formatting
o	Auto-completion with AI or language server support
3. DB ARCHITECTURE & MULTI-TENANT SUPPORT:
•	Split single table into multiple tables or schemas per customer/room.
•	Use relational links between users, rooms, and code history for better tracking.
•	Easier to manage large-scale data and maintain audit logs.
•	Periodic background saves to DB to prevent data loss.
•	Integrate with code history and multi-user edits.
4. ADVANCED AUTOCOMPLETE:
•	Replace current API with context-aware, AI-driven suggestions.
•	Supports multiple programming languages and smart code snippets.
5. MULTI-INSTANCE REAL-TIME SYNC:
•	Introduce Redis Pub/Sub or similar for cross-instance communication.
•	Support horizontal scaling for more users/rooms.

4. FRONTEND FEATURES 

4.1. ROOM CREATION FLOW
•	Users can create a room only after entering a valid username.
•	Username validation rules:
o	Must not be empty.
o	Must be at least 3 characters long.
•	If username is missing or too short → Room creation is blocked with a proper UI message.
•	While creating a room, user must enter the initial room limit.
•	Maximum allowed room limit = 20 users.
•	Limit is validated before room creation; invalid limits are rejected with UI alert.

4.2. ROOM JOIN FUNCTIONALITY
•	Users can join an existing room using:
o	Room ID
o	Username
•	If the room is not full, the user is allowed in or else UI shows a “Room is full” message.
•	If a user with the same username is already present & online in the room:
o	Another user cannot join using the same username.
o	UI shows: "Username already exists".

4.3. CODE EDIOR UI
•	The Room ID is displayed on the editor’s top-right corner.
•	Helps users to share room ID easily with others.
•	Typing indication is implemented to show user typing to other connected users.
•	List users are connected in the room (online and offline using colour differentiation
•	Shows total online, users, limit of the room in the UI.
•	A Save button is provided on the UI, which sends the current code content to the backend.
•	A limit button is provided, which edit the limit with backend validation (new limit has to be greater than current one
•	Disconnect button allows the user to immediately exit:
1.	WebSocket connection closes.
2.	User shown offline to other online users.
