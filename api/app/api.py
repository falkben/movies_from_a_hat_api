"""Main entrypoint"""

import fastapi.openapi.utils
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app import db, movies
from app.patch import get_request_body_with_explode

# monkeypatch to fix swaggerui explode arguments
fastapi.openapi.utils.get_openapi_operation_request_body = get_request_body_with_explode


app = FastAPI()


# todo: remove once we have a proxy
# to verify w/ curl: curl -H "Origin: http://localhost" http://127.0.0.1:8000/ -v
app.add_middleware(
    CORSMiddleware,
    allow_origin_regex=r"http[s]?://(localhost|127.0.0.1)(:[0-9]*)?",
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.on_event("startup")
async def on_startup():
    await db.create_db_and_tables()


app.include_router(movies.router)

if __name__ == "__main__":
    import uvicorn

    uvicorn.run(app)
