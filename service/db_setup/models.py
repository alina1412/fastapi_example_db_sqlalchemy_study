from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import (
    BigInteger,
    Boolean,
    ForeignKey,
    Integer,
    String,
    Text,  # DateTime, TIMESTAMP
    text as sa_text,
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    mapped_column,
    relationship,
)

from service.config import utcnow


class Base(MappedAsDataclass, DeclarativeBase):
    """Subclasses will be converted to dataclasses."""

    pass


class Question(Base):
    __tablename__ = "question"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    answers = relationship("Answer", back_populates="question")

    updated_dt: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default_factory=utcnow,
        server_default=sa_text("TIMEZONE('utc', now())"),
        onupdate=sa_text("TIMEZONE('utc', now())"),
    )


class Answer(Base):
    __tablename__ = "answer"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    text: Mapped[str] = mapped_column(String(255), nullable=True)
    correct: Mapped[bool] = mapped_column(Boolean, server_default="0")
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE")
    )
    question = relationship("Question", back_populates="answers")


class User(Base):
    __tablename__ = "user"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    username: Mapped[str] = mapped_column(
        String(255), unique=True, nullable=False
    )
    password: Mapped[str] = mapped_column(String(255), nullable=False)
    active: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="1"
    )


class Player(Base):
    __tablename__ = "player"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    tg_id: Mapped[int] = mapped_column(BigInteger, unique=True, nullable=False)
    score: Mapped[int] = mapped_column(
        Integer, nullable=False, server_default="0"
    )


class Rounds(Base):
    __tablename__ = "round"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
    asked: Mapped[bool] = mapped_column(Boolean, server_default="False")
    question_id: Mapped[int] = mapped_column(
        ForeignKey("question.id", ondelete="CASCADE")
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("player.tg_id", ondelete="CASCADE")
    )


class TgUpdate(Base):
    __tablename__ = "tg_update"

    id: Mapped[int] = mapped_column(init=False, primary_key=True)
