from datetime import datetime
from typing import Optional, List, Dict, Any
from pydantic import BaseModel, Field, EmailStr

# PUBLIC_INTERFACE
class UserBase(BaseModel):
    username: str = Field(..., description="Unique user name")

# PUBLIC_INTERFACE
class UserCreate(UserBase):
    email: EmailStr = Field(..., description="User email")
    password: str = Field(..., description="User password")

# PUBLIC_INTERFACE
class UserLogin(BaseModel):
    username: str = Field(..., description="Unique username")
    password: str = Field(..., description="User password")

# PUBLIC_INTERFACE
class UserOut(UserBase):
    id: int
    email: EmailStr
    created_at: datetime
    wins: int
    losses: int
    draws: int
    elo: int

    class Config:
        orm_mode = True

# PUBLIC_INTERFACE
class Token(BaseModel):
    access_token: str
    token_type: str

# PUBLIC_INTERFACE
class MoveRequest(BaseModel):
    game_id: int
    from_square: str = Field(..., description="Chess notation of the starting square (e.g., e2)")
    to_square: str = Field(..., description="Chess notation of the ending square (e.g., e4)")

# PUBLIC_INTERFACE
class MoveResponse(BaseModel):
    move_uci: str
    fen: str
    valid: bool
    message: Optional[str] = ""

# PUBLIC_INTERFACE
class GameStartRequest(BaseModel):
    opponent_username: Optional[str] = Field("", description="If blank, triggers matchmaking or AI")
    vs_ai: bool = False

# PUBLIC_INTERFACE
class GameSummary(BaseModel):
    id: int
    white: str
    black: str
    result: Optional[str] = None
    started_at: datetime
    ended_at: Optional[datetime]
    fen: str

# PUBLIC_INTERFACE
class GameDetail(GameSummary):
    moves: List[str]
    history: List[Dict[str, Any]]  # Detailed moves or board states

# PUBLIC_INTERFACE
class MatchmakeResponse(BaseModel):
    status: str
    game_id: Optional[int] = None
    message: Optional[str] = ""

# PUBLIC_INTERFACE
class LeaderboardEntry(BaseModel):
    username: str
    elo: int
    wins: int
    losses: int
    draws: int

# PUBLIC_INTERFACE
class Leaderboard(BaseModel):
    leaderboard: List[LeaderboardEntry]

