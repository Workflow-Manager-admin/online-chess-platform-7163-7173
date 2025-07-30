from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.api.routers_user import router as user_router
from src.api.routers_game import router as game_router
from src.api.routers_matchmaking import router as matchmaking_router
from src.api.db import init_db

app = FastAPI(
    title="Chess API",
    description="Backend API for Online Chess Platform!",
    version="1.0.0"
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.on_event("startup")
def on_startup():
    init_db()

@app.get("/")
def health_check():
    """Health Check endpoint for the Chess API."""
    return {"message": "Healthy"}

app.include_router(user_router)
app.include_router(game_router)
app.include_router(matchmaking_router)

