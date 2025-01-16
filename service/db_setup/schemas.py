from dataclasses import dataclass
from datetime import datetime


@dataclass
class QuestionDto:
    id: int
    text: str
    active: int
    answers: list
    updated_dt: datetime


@dataclass
class AnswerDto:
    id: int
    text: str
    correct: bool
    question_id: int


@dataclass
class UserDto:
    id: int
    username: str
    password: str
    active: str
