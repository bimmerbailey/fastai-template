from typing import Annotated, AsyncIterator

from fastapi import Depends, Request
from sqlalchemy.ext.asyncio import AsyncEngine
from sqlmodel.ext.asyncio.session import AsyncSession

from fastai.database.core import get_db_session


def get_db_engine(request: Request) -> AsyncEngine:
    return request.app.state.db_engine


async def get_session(
    engine: Annotated[AsyncEngine, Depends(get_db_engine)],
) -> AsyncIterator[AsyncSession]:
    async for sess in get_db_session(engine):
        yield sess


SessionDep = Annotated[AsyncSession, Depends(get_session)]
