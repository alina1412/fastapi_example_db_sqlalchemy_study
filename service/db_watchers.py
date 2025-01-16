import sqlalchemy as sa
from sqlalchemy.dialects.postgresql import insert as ps_insert
from sqlalchemy.dialects.mysql import insert as mysql_insert

# from sqlalchemy import select, update, or_, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import joinedload  # , lazyload, load_only
from sqlalchemy.sql.expression import false, true

from service.config import logger, db_settings
from service.db_setup.models import (
    Answer,
    Player,
    Question,
    Rounds,
    TgUpdate,
    User,
)
from service.db_setup.schemas import AnswerDto, QuestionDto
from service.schemas import QuestionListRequest


class QuestionDb:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_question(self, vals) -> int | None:
        query = sa.insert(Question).values(**vals)
        result = await self.session.execute(query)
        return result.lastrowid if result.lastrowid else None
        # logger.info("added %s", result.returned_defaults[0])

    async def remove_question(self, id_: int) -> int:
        query = sa.delete(Question).where(*(Question.id == id_,))
        result = await self.session.execute(query)
        return result.rowcount

    async def edit_question_by_id(
        self, id_: int, vals: dict
    ) -> QuestionDto | None:
        vals = {k: v for k, v in vals.items() if v is not None}
        if not vals:
            return None
        query = (
            sa.update(Question)
            .where(Question.id == id_)
            .values(**vals)
            .returning(Question)
        )
        elem = (await self.session.execute(query)).scalar_one_or_none()
        return (
            QuestionDto(
                id=elem.id,
                text=elem.text,
                active=elem.active,
                answers=[],
                updated_dt=elem.updated_dt,
            )
            if elem
            else None
        )

    async def find_correct_answers(self, question_id: int) -> list[AnswerDto]:
        query = sa.select(Answer).where(
            (Answer.question_id == question_id) & (Answer.correct == True)
        )
        result = await self.session.execute(query)
        res = result.scalars().all()
        return [
            AnswerDto(
                id=elem.id,
                text=elem.text,
                correct=elem.correct,
                question_id=elem.question_id,
            )
            for elem in res
        ]

    async def get_question_by_id(self, id_: int) -> QuestionDto | None:
        query = sa.select(Question).where(Question.id == id_)
        result = await self.session.execute(query)
        res = result.scalars().first()
        return (
            QuestionDto(
                id=res.id,
                text=res.text,
                active=res.active,
                answers=[],
                updated_dt=res.updated_dt,
            )
            if res
            else None
        )

    async def get_questions(
        self, data: QuestionListRequest
    ) -> list[QuestionDto]:
        data = data.model_dump()
        orders = {
            "id": Question.id.desc(),
            "updated_dt": Question.updated_dt.desc(),
            "active": Question.active.desc(),
        }
        order = orders[data["order"]] if data["order"] in orders else None

        query = (
            sa.select(Question)
            .where(Question.active == data["active"])
            .order_by(order)
            .limit(data["limit"])
            .offset(data["offset"])
        )
        if data["text"]:
            query = query.where(Question.text.ilike(f"%{data['text']}%"))
        result = await self.session.execute(query)
        res = result.scalars().all()
        return [
            QuestionDto(
                id=elem.id,
                text=elem.text,
                active=elem.active,
                answers=[],
                updated_dt=elem.updated_dt,
            )
            for elem in res
        ]

    async def get_questions_with_answers(
        self, data: QuestionListRequest
    ) -> list[QuestionDto]:
        data = data.model_dump()
        order = Question.id.desc() if data["order"] == "id" else None

        query = (
            sa.select(Question, Answer)
            .where(Question.active == data["active"])
            .order_by(order)
            .limit(data["limit"])
            .offset(data["offset"])
        )
        if data["text"]:
            query = query.where(Question.text.ilike(f"%{data['text']}%"))
        if data.get("question_id"):
            query = query.where(Question.id == data["question_id"])

        query = query.options(joinedload(Question.answers)).where(
            Question.id == Answer.question_id
        )
        result = await self.session.execute(query)
        result = result.scalars().unique()
        return [
            QuestionDto(
                id=question.id,
                text=question.text,
                active=question.active,
                answers=[
                    AnswerDto(
                        id=res.id,
                        text=res.text,
                        correct=res.correct,
                        question_id=res.question_id,
                    )
                    for res in question.answers
                ],
                updated_dt=question.updated_dt,
            )
            for question in result
        ]


class AnswerDb:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_answer(self, vals) -> int | None:
        query = sa.insert(Answer).values(**vals)
        result = await self.session.execute(query)
        return result.lastrowid if result.lastrowid else None

    async def remove_answer(self, id_: int) -> int:
        query = sa.delete(Answer).where(Answer.id == id_)
        result = await self.session.execute(query)
        return result.rowcount

    async def get_answer_by_id(self, ans_id: int) -> AnswerDto | None:
        query = sa.select(Answer).where(Answer.id == ans_id)
        result = await self.session.execute(query)
        res = result.scalars().first()
        return (
            AnswerDto(
                id=res.id,
                text=res.text,
                correct=res.correct,
                question_id=res.question_id,
            )
            if res
            else None
        )

    async def get_answers_for_question(
        self, question_id: int
    ) -> list[AnswerDto]:
        query = sa.select(Answer).where(Answer.question_id == question_id)
        result = await self.session.execute(query)
        res = result.scalars().all()
        return [
            AnswerDto(
                id=elem.id,
                text=elem.text,
                correct=elem.correct,
                question_id=elem.question_id,
            )
            for elem in res
        ]


class TgDb:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def update_tg_id(self, id_: int):
        query = sa.update(TgUpdate).values(**{"id": id_})
        await self.session.execute(query)

    async def get_last_tg_id(self):
        query = sa.select(TgUpdate.id).limit(1)
        res = (await self.session.execute(query)).scalar_one_or_none()
        return res


class UserDb:
    model = None

    def __init__(self, model) -> None:
        self.model = model

    async def select_all(self, session):
        conds = (1 == 1,)
        query = sa.select(self.model).where(*conds)
        result = await session.execute(query)
        res = result.scalars().all()
        data = [{"username": u.username, "id": u.id} for u in res]
        return data

    async def put(self, session, username, password):
        vals = {"username": username, "password": password}
        if "postgresql" in db_settings["db_driver"]:
            query = (
                ps_insert(self.model).values(**vals).on_conflict_do_nothing()
            )
        else:
            query = (
                mysql_insert(self.model).values(**vals).prefix_with("IGNORE")
            )

        result = await session.execute(query)
        return result.lastrowid if result.lastrowid else None

    async def update(self, session):
        vals = {"id": 100, User.active.key: User.active or 0}
        conds = (
            User.id == vals["id"],
            sa.or_(
                User.active == 1,
                User.password.is_(None),
            ),
        )
        # {self.model.active.key: self.model.active or data["active"]}
        if not conds:
            conds = (1 == 1,)  # conds = (User.id == 103,)
        query = (
            sa.update(self.model)
            .where(*conds)
            .values(**vals)
            .returning(self.model.id)
        )
        result = list(await session.execute(query))
        return result

    async def delete(self, session, id_):
        query = sa.delete(self.model).where(*(User.id == id_,))
        result = await session.execute(query)
        # result.rowcount
        return


class GameDb:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new_rounds(self, user_tg_id: int, amount: int = 5) -> None:
        """To Round model -> question_id, user_tg_id"""
        sub_query_choice = (
            sa.select(Question.id, sa.cast(user_tg_id, sa.Integer))
            .order_by(sa.func.random())
            .limit(amount)
        )
        query_insert_rounds = (
            sa.insert(Rounds).from_select(
                ["question_id", "player_id"], sub_query_choice
            )
            # .returning(Rounds.id)
        )
        try:
            result = await self.session.execute(query_insert_rounds)
        except IntegrityError as err:
            logger.error("error ", exc_info=err)
            raise err

    async def delete_old_rounds(self, user_tg_id: int) -> None:
        query = sa.delete(Rounds).where(
            *(Rounds.asked == true(), Rounds.player_id == user_tg_id)
        )
        await self.session.execute(query)

    async def raise_score(self, user_tg_id: int) -> int | None:
        upd_query = (
            sa.update(Player)
            .where(Player.tg_id == user_tg_id)
            .values(**{"score": Player.__table__.c.score + 1})
            # .returning(Player.score)
        )
        await self.session.execute(upd_query)

        select_query = sa.select(Player.score).where(Player.tg_id == user_tg_id)
        return (await self.session.execute(select_query)).scalar_one_or_none()

    async def get_next_question_id(self, user_tg_id: int) -> int | None:
        query = sa.select(Rounds.question_id).where(
            Rounds.player_id == user_tg_id, Rounds.asked == false()
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def mark_question_answered(
        self, question_id: int, user_tg_id: int
    ) -> None:
        query = (
            sa.update(Rounds)
            .where(
                Rounds.player_id == user_tg_id,
                Rounds.question_id == question_id,
            )
            .values(asked=true())
        )
        await self.session.execute(query)

    async def create_player(self, user_tg_id: int) -> int | None:
        if "postgresql" in db_settings["db_driver"]:
            query = (
                ps_insert(Player)
                .values(**{"tg_id": user_tg_id})
                .on_conflict_do_nothing()
                .returning(Player.id)
            )
        else:
            query = (
                mysql_insert(Player)
                .values(**{"tg_id": user_tg_id})
                .prefix_with("IGNORE")
                # .returning(Player.id)
            )
            # result = await self.session.execute(query)
            # if result.rowcount:
            #     inserted_id = (await self.session.execute(sa.text("SELECT LAST_INSERT_ID()"))).scalar()
            #     return inserted_id
        result = await self.session.execute(query)
        return result.lastrowid if result.lastrowid else None

    async def get_score_of_player(self, user_tg_id: int) -> int | None:
        query = sa.select(Player.score).where(Player.tg_id == user_tg_id)
        result = await self.session.execute(query)
        return result.scalars().first()
