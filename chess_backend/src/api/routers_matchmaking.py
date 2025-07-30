from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.models import MatchmakeResponse
from src.api.db import get_db, Game, User
from src.api.security import oauth2_scheme, decode_access_token

router = APIRouter(
    prefix="/matchmaking",
    tags=["matchmaking"]
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

# PUBLIC_INTERFACE
@router.post("/find", response_model=MatchmakeResponse)
def find_match(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Find or create a waiting game slot for matchmaking."""
    waiting_game = db.query(Game).filter(Game.status == "waiting", Game.is_vs_ai == False).filter(Game.white_id != current_user.id).first()
    if waiting_game:
        waiting_game.black_id = current_user.id
        waiting_game.status = "active"
        db.commit()
        db.refresh(waiting_game)
        return MatchmakeResponse(status="matched", game_id=waiting_game.id)
    else:
        game = Game(
            white_id=current_user.id,
            fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
            status="waiting",
            is_vs_ai=False,
            moves=""
        )
        db.add(game)
        db.commit()
        db.refresh(game)
        return MatchmakeResponse(status="waiting", game_id=game.id)

# PUBLIC_INTERFACE
@router.post("/ai", response_model=MatchmakeResponse)
def play_with_ai(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Creates a game with AI as opponent."""
    game = Game(
        white_id=current_user.id,
        black_id=None,
        fen="rnbqkbnr/pppppppp/8/8/8/8/PPPPPPPP/RNBQKBNR w KQkq - 0 1",
        status="active",
        is_vs_ai=True,
        moves=""
    )
    db.add(game)
    db.commit()
    db.refresh(game)
    return MatchmakeResponse(status="active", game_id=game.id)

