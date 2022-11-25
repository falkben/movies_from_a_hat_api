import sqlalchemy.exc
from fastapi import HTTPException
from loguru import logger
from sqlalchemy.future import select
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlmodel.main import SQLModelMetaclass


async def get_object_or_404(session: AsyncSession, model: SQLModelMetaclass, id):
    instance = await session.get(model, id)
    if not instance:
        raise HTTPException(status_code=404, detail=f"{model.__name__} not found")
    return instance


async def get_or_create(session: AsyncSession, model: SQLModelMetaclass, **kwargs):
    instance = (await session.scalars(select(model).filter_by(**kwargs))).first()
    if instance:
        return instance
    else:
        instance = model(**kwargs)
        session.add(instance)
        logger.info(f"Created {model.__name__}: {kwargs}")
        # !possible race condition with session.flush(): Session is already flushing
        await session.flush()
        return instance


# if you need an update_or_create:
# https://github.com/falkben/steam-to-sqlite/blob/ea3873b9daf725e6b58af7ac70e5b8a54087886e/steam2sqlite/handler.py#L32-L48


async def commit(session: AsyncSession):
    """session.commit() with some exception handling"""
    try:
        await session.commit()
    except sqlalchemy.exc.StatementError as exc:
        logger.error(f"Exception during session.commit(): {exc}")
        raise HTTPException(
            422,
            detail="Database error occurred, check params.",
        )
