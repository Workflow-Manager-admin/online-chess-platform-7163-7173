from sqlalchemy import (
    create_engine, Column, Integer, String, DateTime, ForeignKey, Boolean, func, Text
)
from sqlalchemy.orm import declarative_base, sessionmaker, relationship
import os

DATABASE_URL = os.getenv("CHESS_DB_URL", "sqlite:///./chess.db")

Base = declarative_base()
SessionLocal = sessionmaker(autocommit=False, autoflush=False, bind=create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {}))


# PUBLIC_INTERFACE
class User(Base):
    __tablename__ = "users"
    id = Column(Integer, primary_key=True, index=True)
    username = Column(String, unique=True, index=True, nullable=False)
    email = Column(String, unique=True, nullable=False)
    hashed_password = Column(String, nullable=False)
    created_at = Column(DateTime, server_default=func.now())
    wins = Column(Integer, default=0)
    losses = Column(Integer, default=0)
    draws = Column(Integer, default=0)
    elo = Column(Integer, default=1200)

    games_white = relationship("Game", back_populates="white_player", foreign_keys='Game.white_id')
    games_black = relationship("Game", back_populates="black_player", foreign_keys='Game.black_id')


# PUBLIC_INTERFACE
class Game(Base):
    __tablename__ = "games"
    id = Column(Integer, primary_key=True, index=True)
    white_id = Column(Integer, ForeignKey('users.id'))
    black_id = Column(Integer, ForeignKey('users.id'))
    status = Column(String, default="waiting")  # waiting, active, finished
    fen = Column(String, nullable=False)
    moves = Column(Text, default="")  # Move history in UCI, separated by commas
    result = Column(String, nullable=True)
    started_at = Column(DateTime, server_default=func.now())
    ended_at = Column(DateTime, nullable=True)
    is_vs_ai = Column(Boolean, default=False)

    white_player = relationship("User", foreign_keys=[white_id], back_populates="games_white")
    black_player = relationship("User", foreign_keys=[black_id], back_populates="games_black")


# PUBLIC_INTERFACE
def get_db():
    """Yield a DB Session for dependency injection."""
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()


# To auto-create tables (in development)
def init_db():
    engine = create_engine(DATABASE_URL, connect_args={"check_same_thread": False} if "sqlite" in DATABASE_URL else {})
    Base.metadata.create_all(bind=engine)

