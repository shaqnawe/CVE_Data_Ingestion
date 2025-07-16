from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select, cast, String
from db import get_session
from models import CVEItem, CVEPage
import etl
import json
from cache import redis_client
from sqlalchemy import func
from limiter import limiter

router = APIRouter()


@router.post("/fetch-nvd-feed")
@limiter.limit("10/minute")
def fetch_nvd(request: Request):
    # print(request.client.host)
    etl.fetch_and_save_feed()
    cve_items = etl.parse_cve_items()
    return {"message": f"Fetched and parsed {len(cve_items)} CVE entries"}


@router.post("/ingest-nvd-feed")
@limiter.limit("10/minute")
def ingest_nvd_feed(request: Request):
    etl.fetch_and_save_feed()
    etl.transform_and_load()
    return {"message": "NVD feed fetched, parsed, and loaded into database"}


@router.get("/cves/{cve_id}", response_model=CVEItem)
@limiter.limit("1/minute")
def get_cve_by_id(
    request: Request, cve_id: str, session: Session = Depends(get_session)
):
    statement = select(CVEItem).where(CVEItem.cve_id == cve_id)
    result = session.exec(statement).first()
    if not result:
        raise HTTPException(status_code=404, detail="CVE not found")
    return result


@router.get("/cves/", response_model=CVEPage)
@limiter.limit("10/minute")
def list_cves(
    request: Request,
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
):
    capped_limit = min(limit, 100)
    total = session.exec(select(func.count()).select_from(CVEItem)).one()
    cache_key = f"cves:skip={skip}:limit={limit}"
    cached = redis_client.get(cache_key)
    if cached:
        print("Serving from Redis cache!")
        # redis_client is configured to return decoded result
        # by default so adding ignore to avoid type warning
        return CVEPage(**json.loads(cached))  # type:ignore
    statement = select(CVEItem).offset(skip).limit(limit)
    items = list(session.exec(statement).all())
    # Cache for 5 minutes
    page = CVEPage(total=total, skip=skip, limit=capped_limit, items=items)
    redis_client.setex(cache_key, 300, page.model_dump_json())
    return page


@router.get("/cves/by-severity/", response_model=list[CVEItem])
def get_cves_by_severity(
    severity: str,
    skip: int = 0,
    limit: int = 10,
    session: Session = Depends(get_session),
):
    statement = (
        select(CVEItem).where(CVEItem.severity == severity).offset(skip).limit(limit)
    )
    results = session.exec(statement).all()
    return results


@router.get("/cves/search/", response_model=list[CVEItem])
def search_cves(
    query: str, skip: int = 0, limit: int = 10, session: Session = Depends(get_session)
):
    statement = (
        select(CVEItem)
        .where(cast(CVEItem.description, String).ilike(f"%{query}%"))
        .offset(skip)
        .limit(limit)
    )
    results = session.exec(statement).all()
    return results
