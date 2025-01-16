from contextlib import asynccontextmanager
import uvicorn
from fastapi import FastAPI
import asyncio
from service.endpoints.data_handlers import api_router as data_routes
from service.endpoints.game_handlers import api_router as game_routes
from service.endpoints.tg_handlers import api_router as tg_routes


from service.config import logger


class BackgroundTask:
    async def long_running_task(self):
        await asyncio.sleep(10)


bgtask = BackgroundTask()


@asynccontextmanager
async def lifespan(app: FastAPI):
    task = asyncio.create_task(bgtask.long_running_task())
    yield
    task.cancel()
    try:
        await task
    except asyncio.CancelledError:
        logger.error("lifespan(): long_running_task is cancelled now")


app = FastAPI(lifespan=lifespan)


list_of_routes = [data_routes, tg_routes, game_routes]
for route in list_of_routes:
    app.include_router(route)


if __name__ == "__main__":
    uvicorn.run("service.__main__:app", host="0.0.0.0", port=8000, reload=True)
