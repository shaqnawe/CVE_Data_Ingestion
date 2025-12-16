from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from slowapi import _rate_limit_exceeded_handler
from slowapi.errors import RateLimitExceeded
from backend.routes.cve_routes import router as cve_router
from backend.routes.auth_routes import router as auth_router
from backend.routes.elasticsearch_routes import router as elasticsearch_router
from backend.limiter import limiter

app = FastAPI(title="CVE Data Ingestion Pipeline")
app.state.limiter = limiter
app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)  # type: ignore

# CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:5173", "http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(cve_router)
app.include_router(auth_router)
app.include_router(elasticsearch_router)


@app.get("/")
def read_root():
    return {"status": "ok"}
