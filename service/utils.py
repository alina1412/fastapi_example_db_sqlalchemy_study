from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession

from service.config import logger
from service.db_setup.schemas import AnswerDto, QuestionDto
from service.db_watchers import AnswerDb, QuestionDb
from service.schemas import (
    AnswerInResponse,
    AnswerRequest,
    AnswerSubmitRequest,
    IsCorrectAnsResponse,
    QuestionAddRequest,
    QuestionEditRequest,
    QuestionListRequest,
    QuestionResponseInQuiz,
)


class QuestionsManager:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_question(self, data: QuestionAddRequest):
        vals = data.model_dump()
        return await QuestionDb(self.session).add_question(vals)

    # async def edit_add_question(self, data: QuestionEditRequest):
    #     vals = data.model_dump()
    #     return await QuestionDb(self.session).add_question(vals)

    async def remove_question(self, id_: int):
        return await QuestionDb(self.session).remove_question(id_)

    async def edit_question_by_id(self, vals: dict) -> int:
        id_ = vals.pop("id")
        res = await QuestionDb(self.session).edit_question_by_id(id_, vals)
        return res.id if res else None

    async def find_correct_answers(self, question_id: int) -> list[AnswerDto]:
        return await QuestionDb(self.session).find_correct_answers(question_id)

    async def compare_correct_answers(
        self, params: AnswerSubmitRequest
    ) -> IsCorrectAnsResponse | None:
        question_id, user_ans_ids = params.question_id, params.answer_ids
        if not user_ans_ids:
            return None
        corr_answers = await QuestionDb(self.session).find_correct_answers(
            question_id
        )
        if not corr_answers:
            return None
        is_correct = sorted([r.id for r in corr_answers]) == sorted(
            user_ans_ids
        )
        return IsCorrectAnsResponse(
            correct=is_correct,
            answers=[
                AnswerInResponse(id=ans.id, text=ans.text, correct=ans.correct)
                for ans in corr_answers
            ],
        )

    async def get_question_by_id(self, id_: int) -> QuestionDto | None:
        return await QuestionDb(self.session).get_question_by_id(id_)

    async def get_questions(
        self, data: QuestionListRequest
    ) -> list[QuestionDto]:
        return await QuestionDb(self.session).get_questions(data)

    def convert_quiz_response(self, res) -> dict:
        responses = {}
        for question in res:
            if question.id not in responses:
                responses[question.id] = QuestionResponseInQuiz(
                    text=question.text,
                    id=question.id,
                    active=question.active,
                    answers=[
                        AnswerInResponse(
                            id=answer.id,
                            text=answer.text,
                            correct=answer.correct,
                        )
                        for answer in question.answers
                    ],
                )
        return responses

    async def get_questions_with_answers(
        self, data: QuestionListRequest
    ) -> dict:
        res = await QuestionDb(self.session).get_questions_with_answers(data)
        responses = self.convert_quiz_response(res)
        return responses


class AnswersManager:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_answer(self, data: AnswerRequest):
        vals = data.model_dump()
        try:
            res = await AnswerDb(self.session).add_answer(vals)
        except IntegrityError as err:
            logger.error("error ", exc_info=err)
            raise err
        return res  # res[0].id if res else None

    async def remove_answer(self, id_: int):
        return await AnswerDb(self.session).remove_answer(id_)

    async def get_answer_by_id(self, ans_id: int) -> AnswerDto | None:
        return await AnswerDb(self.session).get_answer_by_id(ans_id)

    async def get_answers_for_question(
        self, question_id: int
    ) -> list[AnswerDto]:
        return await AnswerDb(self.session).get_answers_for_question(
            question_id
        )


"""
class GameManager:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session
"""
