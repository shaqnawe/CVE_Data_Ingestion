from fastapi import FastAPI
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from routes.cve_routes import router as cve_router
from limiter import limiter

app = FastAPI(title="CVE Data Ingestion Pipeline")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore
app.include_router(cve_router)


@app.get("/")
def read_root():
    return {"status": "ok"}
