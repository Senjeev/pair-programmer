from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from app.core.database import engine, Base
from app.routers import rooms, autocomplete, websockets
import logging

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

app = FastAPI(title="Pair Programming App")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(rooms.router)
app.include_router(autocomplete.router)
app.include_router(websockets.router)

@app.on_event("startup")
async def startup_event():
    try:
        Base.metadata.create_all(bind=engine)
        logger.info("Tables created successfully.")
    except Exception:
        logger.exception("Error creating tables")