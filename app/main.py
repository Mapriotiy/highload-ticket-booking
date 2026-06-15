from fastapi import FastAPI

from app.core.config import settings

app = FastAPI(
    title=settings.app_name,
    version="1.0",
    debug=settings.app_debug,
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status":"ok"}