from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from src.api.models import (
    MoveRequest, MoveResponse, GameDetail, GameStartRequest,
    GameSummary
)
from src.api.db import get_db, User, Game
from src.api.security import oauth2_scheme, decode_access_token
from datetime import datetime
from typing import List
import chess

router = APIRouter(
    prefix="/games",
    tags=["games"]
)

def get_current_user(token: str = Depends(oauth2_scheme), db: Session = Depends(get_db)):
    payload = decode_access_token(token)
    user = db.query(User).filter(User.username == payload.get("sub")).first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    return user

INITIAL_FEN = chess.STARTING_FEN

# PUBLIC_INTERFACE
@router.post("/", response_model=GameSummary)
def start_game(request: GameStartRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    """Create a new game vs AI or wait/match vs another player."""
    if request.vs_ai:
        game = Game(
            white_id=current_user.id,
            black_id=None,
            is_vs_ai=True,
            fen=INITIAL_FEN,
            status="active",
            moves=""
        )
        db.add(game)
        db.commit()
        db.refresh(game)
        return GameSummary(
            id=game.id,
            white=current_user.username,
            black="AI",
            result=None,
            started_at=game.started_at,
            ended_at=None,
            fen=game.fen
        )
    else:
        # Find another waiting player
        waiting = db.query(Game).filter_by(status="waiting", is_vs_ai=False).filter(Game.white_id != current_user.id).first()
        if waiting:
            waiting.black_id = current_user.id
            waiting.status = "active"
            db.commit()
            db.refresh(waiting)
            white = db.query(User).filter(User.id == waiting.white_id).first()
            return GameSummary(
                id=waiting.id,
                white=white.username,
                black=current_user.username,
                result=None,
                started_at=waiting.started_at,
                ended_at=None,
                fen=waiting.fen
            )
        else:
            game = Game(
                white_id=current_user.id,
                fen=INITIAL_FEN,
                status="waiting",
                is_vs_ai=False,
                moves=""
            )
            db.add(game)
            db.commit()
            db.refresh(game)
            return GameSummary(
                id=game.id,
                white=current_user.username,
                black="TBD",
                result=None,
                started_at=game.started_at,
                ended_at=None,
                fen=game.fen
            )

# PUBLIC_INTERFACE
@router.post("/move", response_model=MoveResponse)
def make_move(req: MoveRequest, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == req.game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    board = chess.Board(game.fen)
    move_uci = req.from_square + req.to_square
    try:
        move = chess.Move.from_uci(move_uci)
        if move in board.legal_moves:
            board.push(move)
            moves_list = game.moves.split(",") if game.moves else []
            moves_list.append(move.uci())
            game.moves = ",".join(moves_list)
            game.fen = board.fen()
            # Simple victory check
            if board.is_game_over():
                game.status = "finished"
                game.result = board.result()
                game.ended_at = datetime.now()
            db.commit()
            return MoveResponse(
                move_uci=move.uci(),
                fen=board.fen(),
                valid=True,
                message="Move executed"
            )
        else:
            return MoveResponse(
                move_uci=move_uci,
                fen=game.fen,
                valid=False,
                message="Illegal move"
            )
    except ValueError:
        return MoveResponse(
            move_uci=move_uci,
            fen=game.fen,
            valid=False,
            message="Invalid move format"
        )

# PUBLIC_INTERFACE
@router.get("/{game_id}", response_model=GameDetail)
def get_game(game_id: int, db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    game = db.query(Game).filter(Game.id == game_id).first()
    if not game:
        raise HTTPException(status_code=404, detail="Game not found")
    white = db.query(User).filter(User.id == game.white_id).first()
    black = db.query(User).filter(User.id == game.black_id).first() if game.black_id else None
    moves_list = game.moves.split(",") if game.moves else []
    return GameDetail(
        id=game.id,
        white=white.username if white else "AI",
        black=black.username if black else "AI",
        result=game.result,
        started_at=game.started_at,
        ended_at=game.ended_at,
        fen=game.fen,
        moves=moves_list,
        history=[] # Future extension: board states per move
    )

# PUBLIC_INTERFACE
@router.get("/history/me", response_model=List[GameSummary])
def my_game_history(db: Session = Depends(get_db), current_user: User = Depends(get_current_user)):
    games = db.query(Game).filter(
        (Game.white_id == current_user.id) | (Game.black_id == current_user.id)
    ).order_by(Game.started_at.desc()).all()
    out = []
    for game in games:
        white = db.query(User).filter(User.id == game.white_id).first()
        black = db.query(User).filter(User.id == game.black_id).first() if game.black_id else None
        out.append(GameSummary(
            id=game.id,
            white=white.username if white else "AI",
            black=black.username if black else "AI",
            result=game.result,
            started_at=game.started_at,
            ended_at=game.ended_at,
            fen=game.fen
        ))
    return out

# PUBLIC_INTERFACE
@router.get("/leaderboard", response_model=List[dict])
def get_leaderboard(db: Session = Depends(get_db), limit: int = 10):
    users = db.query(User).order_by(User.elo.desc()).limit(limit).all()
    return [{"username": u.username, "elo": u.elo, "wins": u.wins, "losses": u.losses, "draws": u.draws} for u in users]

