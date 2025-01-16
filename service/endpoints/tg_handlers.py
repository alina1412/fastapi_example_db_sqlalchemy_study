from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.ext.asyncio import AsyncSession

from service.db_setup.db_settings import get_session
from service.db_watchers import TgDb
from service.schemas import TgUpdateIdRequest

api_router = APIRouter(
    prefix="",
    tags=["private"],
)


@api_router.put(
    "/tg.update",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def tg_update(
    upd_data: TgUpdateIdRequest,
    session: AsyncSession = Depends(get_session),
):
    """Handler tg.update."""
    tg_accessor = TgDb(session)
    await tg_accessor.update_tg_id(upd_data.update_id)
    return {"success": "1"}


@api_router.get(
    "/tg.get_update_id",
    responses={
        status.HTTP_400_BAD_REQUEST: {"description": "Bad request"},
        status.HTTP_422_UNPROCESSABLE_ENTITY: {"description": "Bad request"},
    },
)
async def get_update_id(session: AsyncSession = Depends(get_session)):
    """Handler tg.get_update_id."""
    tg_accessor = TgDb(session)
    id_ = await tg_accessor.get_last_tg_id()
    return {"update_id": id_}
