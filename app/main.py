from fastapi import FastAPI, HTTPException
from sqlalchemy import text
from sqlalchemy.exc import SQLAlchemyError

from app.core.config import settings
from app.db.session import engine

app = FastAPI(
    title=settings.app_name,
    version="1.0",
    debug=settings.app_debug,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status":"ok"}

@app.get("/health/db")
async def database_health_check() -> dict[str, str]:
    try:
        async with engine.connect() as connection:
            await connection.execute(text("SELECT 1"))
    except SQLAlchemyError as exc:
        raise HTTPException(
            status_code=503,
            detail="Database is unavailable",
        ) from exc

    return {
        "status": "ok",
        "database": "connected",
    }