from datetime import datetime
from enum import Enum
from typing import Any

from pydantic import BaseModel, Field, RootModel


class UserInput(BaseModel):
    username: str


class QuestionOrderSchema(str, Enum):
    id = "id"
    active = "active"
    updated_dt = "updated_dt"


class QuestionListRequest(BaseModel):
    question_id: int | None = Field(description="id of a question", default=0)
    text: str | None = Field(description="search by text", default=None)
    active: int | None = Field(description="if question is active", default=1)
    order: QuestionOrderSchema | None = Field(
        description="order of results", default="id"
    )
    offset: int | None = Field(description="offset to show on page", default=0)
    limit: int | None = Field(description="limit to show on page", default=50)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "question",
                "active": 1,
                "id": None,
                "order": "updated_dt",
                "offset": 0,
                "limit": 50,
            }
        }


class QuestionGetOneRequest(BaseModel):
    question_id: int | None = Field(description="id of a question", default=0)
    tg_id: int = Field(description="tg_id of a player")


class QuestionAddRequest(BaseModel):
    text: str = Field(description="text", min_length=1, max_length=255)
    active: int | None = Field(description="if question is active", default=1)

    class Config:
        json_schema_extra = {
            "example": {
                "text": "question1",
                "active": 1,
            }
        }


class QuestionEditRequest(BaseModel):
    id: int = Field(description="id of a question")
    text: str | None = Field(
        description="text", min_length=1, max_length=255, default=None
    )
    active: int | None = Field(
        description="if question is active", default=None
    )

    class Config:
        json_schema_extra = {
            "example": {
                "text": "question1",
                "active": 1,
                "id": 1,
            }
        }


class QuestionResponse(BaseModel):
    id: int = Field(description="id of a question")
    text: str = Field(description="text")
    active: int = Field(description="if question is active")
    updated_dt: datetime = Field(description="date")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "text": "question1",
                "active": 1,
                "updated_dt": "2024-09-10T08:19:54.531503+00:00",
            }
        }


class QuizListResponse(BaseModel):
    id: int = Field(description="id of a question")
    text: str = Field(description="text")
    active: int = Field(description="if question is active")
    answers: list[Any]


class AnswerRequest(BaseModel):
    id: int | None = Field(description="id of an answer", default=None)
    text: str = Field(description="text", min_length=1, max_length=50)
    correct: bool = Field(description="if answer is correct")
    question_id: int = Field(description="id of a question")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "text": "answer",
                "correct": True,
                "question_id": 1,
            }
        }


class AnswerAddRequest(BaseModel):
    text: str = Field(
        example="answer 1", description="text", min_length=1, max_length=50
    )
    correct: bool = Field(example=True, description="if answer is correct")
    question_id: int = Field(example=1, description="id of a question")

    class Config:
        json_schema_extra = {
            "example": {"text": "answer", "correct": True, "question_id": 1}
        }


class AnswerSubmitRequest(BaseModel):
    question_id: int = Field(description="id of a question")
    answer_ids: list[int] = Field(
        default_factory=list, min_length=0
    )  # AnswersList

    class Config:
        json_schema_extra = {"example": {"answer_ids": [1], "question_id": 1}}


class AnswerResponse(BaseModel):
    id: int = Field(description="id of an answer")
    text: str = Field(description="text")
    correct: bool = Field(description="if answer is correct")
    question_id: int = Field(description="id of a question")

    class Config:
        json_schema_extra = {
            "example": {
                "id": 1,
                "text": "answer",
                "correct": True,
                "question_id": 1,
            }
        }


class TgPlayerIdRequest(BaseModel):
    tg_id: int = Field(description="tg_id")


class TgUpdateIdRequest(BaseModel):
    update_id: int = Field(description="update_id")

    class Config:
        json_schema_extra = {
            "example": {
                "update_id": 0,
            }
        }


class AnswerInResponse(BaseModel):
    id: int
    text: str
    correct: bool


class IsCorrectAnsResponse(BaseModel):
    correct: bool
    answers: list[AnswerInResponse]


class ScoreResponse(BaseModel):
    score: int


class QuestionIdResponse(BaseModel):
    question_id: int = Field(description="question_id")


class QuestionResponseInQuiz(BaseModel):
    id: int
    text: str
    active: int
    answers: list[AnswerInResponse]


class QuizResponse(RootModel):
    root: dict[int, QuestionResponseInQuiz]


class DeleteResponse(BaseModel):
    deleted_rows: int = Field(description="number of deleted rows")

    class Config:
        json_schema_extra = {
            "example": {
                "deleted_rows": 1,
            }
        }


class AnswerAddResponse(BaseModel):
    created: int = Field(description="id of created answer")

    class Config:
        json_schema_extra = {
            "example": {
                "created": 1,
            }
        }


class QuestionAddResponse(BaseModel):
    created: int = Field(description="id of created question")

    class Config:
        json_schema_extra = {
            "example": {
                "created": 1,
            }
        }
