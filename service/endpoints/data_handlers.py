from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_setup.db_settings import get_session
from service.errors import AnswerNotAddedError
from service.schemas import (
    AnswerAddRequest,
    AnswerAddResponse,
    AnswerSubmitRequest,
    DeleteResponse,
    IsCorrectAnsResponse,
    QuestionAddRequest,
    QuestionAddResponse,
    QuestionEditRequest,
    QuestionListRequest,
    QuestionResponse,
    QuizResponse,
)
from service.utils import AnswersManager, QuestionsManager

api_router = APIRouter(
    prefix="/v1",
    tags=["quiz"],
)


@api_router.get(
    "/show-quiz",
    response_model=QuizResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def show_quiz(
    params: QuestionListRequest = Depends(),
    session: AsyncSession = Depends(get_session),  # type: ignore
):
    """Show quiz-test page."""
    data = QuestionListRequest(**params.__dict__)
    q_manager = QuestionsManager(session)
    questions = await q_manager.get_questions_with_answers(data)
    return questions if questions else {}


@api_router.post(
    "/questions",
    response_model=list[QuestionResponse],
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def get_questions(
    data: QuestionListRequest, session: AsyncSession = Depends(get_session)
) -> list[QuestionResponse]:
    """Get_questions"""
    q_manager = QuestionsManager(session)
    questions = await q_manager.get_questions(data)
    return questions if questions else []


@api_router.post(
    "/add-question",
    status_code=status.HTTP_201_CREATED,
    response_model=QuestionAddResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def add_question(
    data: QuestionAddRequest, session: AsyncSession = Depends(get_session)
):
    """Request for add-question."""
    q_manager = QuestionsManager(session)
    id_ = await q_manager.add_question(data)
    if id_:
        return {"created": id_}
    raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")


@api_router.put(
    "/edit-question",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def edit_question(
    params=Depends(QuestionEditRequest),
    session: AsyncSession = Depends(get_session),
):
    """Request for edit_question."""
    q_manager = QuestionsManager(session)
    edit_question_data = params.model_dump()
    res = await q_manager.edit_question_by_id(edit_question_data)
    return {"edited": res}


@api_router.delete(
    "/delete-question",
    response_model=DeleteResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def delete_question(
    id_: int,
    session: AsyncSession = Depends(get_session),
):
    """Request for delete_question."""
    q_manager = QuestionsManager(session)
    res = await q_manager.remove_question(id_)
    return {"deleted_rows": res}


@api_router.post(
    "/add-answer",
    response_model=AnswerAddResponse,
    status_code=status.HTTP_201_CREATED,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def add_answer(
    data: AnswerAddRequest, session: AsyncSession = Depends(get_session)
):
    """Request for add-answer."""
    a_manager = AnswersManager(session)
    try:
        id_ = await a_manager.add_answer(data)
    except IntegrityError as err:
        text_err = f"answer not added: {AnswerNotAddedError(err).add_detail}"
        logger.error(text_err)
        raise HTTPException(
            status.HTTP_400_BAD_REQUEST,
            text_err,
        ) from err
    return {"created": id_}


@api_router.post(
    "/submit-answer",
    response_model=IsCorrectAnsResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def submit_answer(
    params: AnswerSubmitRequest = Depends(),
    session: AsyncSession = Depends(get_session),
):
    """Request for compare_correct_answer."""
    q_manager = QuestionsManager(session)
    is_corr_ans = await q_manager.compare_correct_answers(params)
    if is_corr_ans is None:
        raise HTTPException(status.HTTP_404_NOT_FOUND, "Not found")
    return is_corr_ans


@api_router.delete(
    "/delete-answer",
    response_model=DeleteResponse,
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def delete_answer(
    id: int,
    session: AsyncSession = Depends(get_session),
):
    """Request for delete_answer."""
    a_manager = AnswersManager(session)
    res = await a_manager.remove_answer(id)
    return {"deleted_rows": res}
