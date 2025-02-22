from collections.abc import Sequence

import sqlalchemy as sa
from sqlalchemy.dialects.mysql import insert as mysql_insert
from sqlalchemy.dialects.postgresql import insert as ps_insert

# from sqlalchemy import select, update, or_, delete
from sqlalchemy.exc import IntegrityError
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload  # , lazyload, load_only
from sqlalchemy.sql.expression import false, true

from service.config import db_settings, logger
from service.db_setup.models import (
    Answer,
    Player,
    Question,
    Rounds,
    TgUpdate,
    User,
)
from service.schemas import QuestionAddRequest, QuestionListRequest


class QuestionDb:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_question(self, data: QuestionAddRequest) -> int | None:
        vals = data.model_dump()
        try:
            question = Question(**vals)
            self.session.add(question)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(question)
        except Exception as exc:
            logger.error("Error adding question: ", exc_info=exc)
            await self.session.rollback()
            return None
        logger.info("added question %s", question.id)
        return question.id

    async def remove_question(self, id_: int) -> int:
        query = sa.delete(Question).filter(Question.id == id_)
        result = await self.session.execute(query)
        await self.session.commit()
        return result.rowcount

    async def edit_question_by_id(
        self, id_: int, vals: dict
    ) -> Question | None:
        vals = {k: v for k, v in vals.items() if v is not None}
        if not vals:
            return None
        query_result = await self.session.get(Question, id_)
        if not query_result:
            return None
        for key, value in vals.items():
            if value is not None:
                setattr(query_result, key, value)
        await self.session.flush()
        return query_result

    async def find_correct_answers(self, question_id: int) -> Sequence[Answer]:
        query = sa.select(Answer).where(
            (Answer.question_id == question_id) & (Answer.correct == true())
        )
        result = await self.session.execute(query)
        return result.scalars().all()

    async def get_question_by_id(self, id_: int) -> Question | None:
        query = (
            sa.select(Question)
            .where(Question.id == id_)
            .options(selectinload(Question.answers))
        )
        result = await self.session.execute(query)
        return result.scalars().first()

    async def get_questions(self, data: QuestionListRequest) -> list[Question]:
        """Without joining answers."""
        data = data.model_dump()
        orders = {
            "id": Question.id.desc(),
            "updated_dt": Question.updated_dt.desc(),
            "active": Question.active.desc(),
        }
        order = orders.get(data["order"], None)

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
        return res

    async def get_questions_with_answers(
        self, data: QuestionListRequest
    ) -> list[Question]:
        data = data.model_dump()
        order = Question.id.desc() if data["order"] == "id" else None

        query = (
            sa.select(Question)
            .where(Question.active == data["active"])
            .options(selectinload(Question.answers))
            .order_by(order)
            .limit(data["limit"])
            .offset(data["offset"])
        )
        if data["text"]:
            query = query.where(Question.text.ilike(f"%{data['text']}%"))
        if data.get("question_id"):
            query = query.where(Question.id == data["question_id"])
        result = await self.session.execute(query)
        return result.scalars().unique()


class AnswerDb:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def add_answer(self, vals) -> int | None:
        try:
            answer = Answer(**vals)
            self.session.add(answer)
            await self.session.flush()
            await self.session.commit()
            await self.session.refresh(answer)
        except Exception as exc:
            logger.error("Error adding answer: ", exc_info=exc)
            await self.session.rollback()
            return None
        logger.info("added answer %s", answer.id)
        return answer.id

    async def remove_answer(self, id_: int) -> int:
        query = sa.delete(Answer).where(Answer.id == id_)
        result = await self.session.execute(query)
        return result.rowcount

    async def get_answer_by_id(self, ans_id: int) -> Answer | None:
        return await self.session.get(Answer, ans_id)

    async def get_answers_for_question(self, question_id: int) -> list[Answer]:
        query = sa.select(Answer).where(Answer.question_id == question_id)
        result = await self.session.execute(query)
        return result.scalars().all()


class TgDb:
    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def update_tg_id(self, id_: int) -> None:
        query = sa.update(TgUpdate).values(id=id_)
        await self.session.execute(query)

    async def get_last_tg_id(self) -> int | None:
        query = sa.select(TgUpdate.id).limit(1)
        res = (await self.session.execute(query)).scalar_one_or_none()
        return res


class UserDb:
    model = None

    def __init__(self, model) -> None:
        self.model = model

    async def select_all(self, session, conds=(True,)):
        query = sa.select(self.model).where(*conds)
        result = await session.execute(query)
        res = result.scalars().all()
        data = [{"username": u.username, "id": u.id} for u in res]
        return data

    async def put(self, session, username, password):
        vals = {"username": username, "password": password}
        if "postgresql" in db_settings["db_driver"]:
            query = (
                ps_insert(self.model)
                .values(**vals)
                .on_conflict_do_nothing()
                .returning(self.model.id)
            )
        else:
            query = (
                mysql_insert(self.model).values(**vals).prefix_with("IGNORE")
            )

        result = await session.execute(query)
        if "postgresql" in db_settings["db_driver"]:
            return result.returned_defaults[0]
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
        query = sa.update(self.model).values(**vals).returning(self.model.id)
        if conds:
            query = query.where(*conds)

        result = list(await session.execute(query))
        return result

    async def delete(self, session, id_):
        query = sa.delete(self.model).where(*(User.id == id_,))
        result = await session.execute(query)
        return result.rowcount


class GameDb:
    session = None

    def __init__(self, session: AsyncSession) -> None:
        self.session = session

    async def create_new_rounds(self, user_tg_id: int, amount: int = 5) -> None:
        """To Round model -> question_id, user_tg_id."""
        sub_query_choice = (
            sa.select(Question.id, sa.cast(user_tg_id, sa.Integer))
            .order_by(sa.func.random())
            .limit(amount)
        )
        query_insert_rounds = sa.insert(Rounds).from_select(
            ["question_id", "player_id"], sub_query_choice
        )
        try:
            await self.session.execute(query_insert_rounds)
        except IntegrityError as err:
            logger.error("error ", exc_info=err)
            raise err

    async def delete_old_rounds(self, user_tg_id: int) -> None:
        query = sa.delete(Rounds).where(
            *(Rounds.asked == true(), Rounds.player_id == user_tg_id)
        )
        await self.session.execute(query)

    async def raise_score(self, user_tg_id: int) -> int | None:
        player_result = (
            (
                await self.session.execute(
                    sa.select(Player).where(Player.tg_id == user_tg_id)
                )
            )
            .scalars()
            .first()
        )
        if not player_result:
            return None
        player_result.score += 1
        await self.session.flush()
        return player_result.score

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
                .values(tg_id=user_tg_id)
                .on_conflict_do_nothing()
                .returning(Player.id)
            )
        else:
            query = (
                mysql_insert(Player)
                .values(tg_id=user_tg_id)
                .prefix_with("IGNORE")
            )
        result = await self.session.execute(query)
        if "postgresql" in db_settings["db_driver"]:
            return result.returned_defaults[0]
        return result.lastrowid if result.lastrowid else None

    async def get_score_of_player(self, user_tg_id: int) -> int | None:
        query = sa.select(Player.score).where(Player.tg_id == user_tg_id)
        result = await self.session.execute(query)
        return result.scalars().first()
