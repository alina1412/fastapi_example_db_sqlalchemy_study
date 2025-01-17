from datetime import datetime

import sqlalchemy as sa
from sqlalchemy import (
    Boolean,
    Column,
    ForeignKey,
    Integer,
    BigInteger,
    String,
    text as sa_text,
    Text,  # DateTime, TIMESTAMP
)
from sqlalchemy.orm import (
    DeclarativeBase,
    Mapped,
    MappedAsDataclass,
    # declarative_base,
    mapped_column,
    relationship,
)

# from sqlalchemy.sql import func
from service.config import utcnow


class Base(DeclarativeBase):
    pass


class Base(MappedAsDataclass, DeclarativeBase):
    """Subclasses will be converted to dataclasses"""

    pass


class Question(Base):
    __tablename__ = "questions"
    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    text: Mapped[str] = mapped_column(Text, nullable=True)
    active: Mapped[int] = mapped_column(Integer, nullable=False, default=1)
    # answers = relationship("Answer", backref="questions")
    answers = relationship("Answer", back_populates="question")
    # answers: Mapped[List["Answer"]] = relationship()
    updated_dt: Mapped[datetime] = mapped_column(
        sa.DateTime(timezone=True),
        default_factory=utcnow,
        server_default=sa_text("TIMEZONE('utc', now())"),
        onupdate=sa_text("TIMEZONE('utc', now())"),
    )


class Answer(Base):
    __tablename__ = "answers"

    id = Column(Integer, primary_key=True)
    text = Column(String(255), nullable=True)
    correct = Column(Boolean, default=0)
    # question_id = Column(Integer, ForeignKey("questions.id", ondelete="CASCADE"))
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    question = relationship("Question", back_populates="answers")


class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True)
    username = Column(String(255), unique=True, nullable=False)
    password = Column(String(255), nullable=False)
    active = Column(Integer, nullable=False, server_default="1")


class Player(Base):
    __tablename__ = "players"

    id = Column(Integer, primary_key=True)
    tg_id = Column(BigInteger, unique=True, nullable=False)
    score = Column(Integer, nullable=False, server_default="0")


class Rounds(Base):
    __tablename__ = "rounds"

    id = Column(Integer, primary_key=True)
    asked = Column(Boolean, server_default="False")
    question_id: Mapped[int] = mapped_column(
        ForeignKey("questions.id", ondelete="CASCADE")
    )
    player_id: Mapped[int] = mapped_column(
        BigInteger, ForeignKey("players.tg_id", ondelete="CASCADE")
    )


class TgUpdate(Base):
    __tablename__ = "tg_update"

    id = Column(Integer, primary_key=True)
