from fastapi import FastAPI

app = FastAPI(
    title="High Load Ticket Booking API",
    version="1.0",
)


@app.get("/health")
def health_check() -> dict[str, str]:
    return {"status":"ok"}