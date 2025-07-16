from fastapi import APIRouter, Depends, HTTPException, Request
from sqlmodel import Session, select, cast, String
from db import get_session
from models import CVEItem, CVEPage
import etl
from sqlalchemy import func
from limiter import limiter
from cache import (
    get_cache,
    set_cache,
    make_cache_key,
    serialize_model,
    deserialize_model,
)

router = APIRouter()


@router.post("/fetch-nvd-feed")
@limiter.limit("10/minute")
def fetch_nvd(request: Request):
    # print(request.client.host)
    fetch_metrics = etl.fetch_and_save_feed()
    cve_items = etl.parse_cve_items()
    return {
        "message": f"Fetched and parsed {len(cve_items)} CVE entries",
        "metrics": fetch_metrics,
    }


@router.post("/ingest-nvd-feed")
@limiter.limit("10/minute")
def ingest_nvd_feed(request: Request):
    pipeline_metrics = etl.run_etl_pipeline()
    return {
        "message": "NVD feed fetched, parsed, and loaded into database",
        "metrics": pipeline_metrics,
    }


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
    cache_key = make_cache_key("cves", skip=skip, limit=limit)
    cached = get_cache(cache_key)
    if cached:
        print("Serving from Redis cache!")
        return deserialize_model(cached, CVEPage)
    statement = select(CVEItem).offset(skip).limit(limit)
    items = list(session.exec(statement).all())
    page = CVEPage(total=total, skip=skip, limit=capped_limit, items=items)
    set_cache(cache_key, serialize_model(page), 300)
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
