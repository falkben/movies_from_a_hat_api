"""Main entrypoint"""

import fastapi.openapi.utils
from fastapi import FastAPI

from app import db, movies
from app.patch import get_request_body_with_explode

# monkeypatch to fix swaggerui explode arguments
fastapi.openapi.utils.get_openapi_operation_request_body = get_request_body_with_explode


app = FastAPI()


@app.on_event("startup")
async def on_startup():
    await db.create_db_and_tables()


app.include_router(movies.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
