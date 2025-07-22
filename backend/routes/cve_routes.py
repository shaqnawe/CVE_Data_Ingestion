from fastapi import APIRouter, Depends, HTTPException, Request, Query
from sqlmodel import Session, select, cast, String
from backend.db import get_session
from backend.models import CVEItem, CVEPage, User
import backend.etl as etl
from sqlalchemy import func, desc, asc
from backend.limiter import limiter
from backend.cache import (
    get_cache,
    set_cache,
    make_cache_key,
    serialize_model,
    deserialize_model,
)
from backend.celery_app import celery_app
from backend.tasks import run_etl_pipeline_task, fetch_nvd_feed_task, transform_and_load_task
from backend.auth import get_current_active_user, require_role
from typing import Optional

router = APIRouter()


@router.post("/fetch-nvd-feed")
@limiter.limit("10/minute")
def fetch_nvd(request: Request, current_user: User = Depends(require_role("admin"))):
    # print(request.client.host)
    fetch_metrics = etl.fetch_and_save_feed()
    cve_items = etl.parse_cve_items()
    return {
        "message": f"Fetched and parsed {len(cve_items)} CVE entries",
        "metrics": fetch_metrics,
    }


@router.post("/ingest-nvd-feed")
@limiter.limit("10/minute")
def ingest_nvd_feed(
    request: Request, current_user: User = Depends(require_role("admin"))
):
    pipeline_metrics = etl.run_etl_pipeline()
    return {
        "message": "NVD feed fetched, parsed, and loaded into database",
        "metrics": pipeline_metrics,
    }


@router.get("/cves/{cve_id}", response_model=CVEItem)
@limiter.limit("1/minute")
def get_cve_by_id(
    request: Request,
    cve_id: str,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
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
    severity: Optional[str] = Query(
        None, description="Filter by severity (HIGH, MEDIUM, LOW)"
    ),
    sort_by: Optional[str] = Query(
        None, description="Sort by field (cvss_v3_score, published_date)"
    ),
    order: Optional[str] = Query("asc", description="Sort order (asc, desc)"),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_active_user),
):
    capped_limit = min(limit, 100)

    # Build base query
    base_query = select(CVEItem)

    # Add severity filter if provided
    if severity and severity.upper() in ["HIGH", "MEDIUM", "LOW"]:
        base_query = base_query.where(CVEItem.severity == severity.upper())

    # Add sorting if provided
    if sort_by and order:
        if sort_by == "cvss_v3_score":
            if order.lower() == "desc":
                base_query = base_query.order_by(desc(CVEItem.cvss_v3_score))
            else:
                base_query = base_query.order_by(asc(CVEItem.cvss_v3_score))
        elif sort_by == "published_date":
            if order.lower() == "desc":
                base_query = base_query.order_by(desc(CVEItem.published_date))
            else:
                base_query = base_query.order_by(asc(CVEItem.published_date))

    # Get total count with filters
    count_query = select(func.count()).select_from(CVEItem)
    if severity and severity.upper() in ["HIGH", "MEDIUM", "LOW"]:
        count_query = count_query.where(CVEItem.severity == severity.upper())
    total = session.exec(count_query).one()

    # Add pagination
    statement = base_query.offset(skip).limit(capped_limit)

    # Cache key includes filter and sort parameters
    cache_key = make_cache_key(
        "cves", skip=skip, limit=limit, severity=severity, sort_by=sort_by, order=order
    )
    cached = get_cache(cache_key)
    if cached:
        print("Serving from Redis cache!")
        return deserialize_model(cached, CVEPage)

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
    query: str,
    skip: int = 0,
    limit: int = 10,
    severity: Optional[str] = Query(
        None, description="Filter by severity (HIGH, MEDIUM, LOW)"
    ),
    sort_by: Optional[str] = Query(
        None, description="Sort by field (cvss_v3_score, published_date)"
    ),
    order: Optional[str] = Query("asc", description="Sort order (asc, desc)"),
    session: Session = Depends(get_session),
):
    # Build base query with search
    base_query = select(CVEItem).where(
        cast(CVEItem.description, String).ilike(f"%{query}%")
    )

    # Add severity filter if provided
    if severity and severity.upper() in ["HIGH", "MEDIUM", "LOW"]:
        base_query = base_query.where(CVEItem.severity == severity.upper())

    # Add sorting if provided
    if sort_by and order:
        if sort_by == "cvss_v3_score":
            if order.lower() == "desc":
                base_query = base_query.order_by(desc(CVEItem.cvss_v3_score))
            else:
                base_query = base_query.order_by(asc(CVEItem.cvss_v3_score))
        elif sort_by == "published_date":
            if order.lower() == "desc":
                base_query = base_query.order_by(desc(CVEItem.published_date))
            else:
                base_query = base_query.order_by(asc(CVEItem.published_date))

    # Add pagination
    statement = base_query.offset(skip).limit(limit)
    results = session.exec(statement).all()
    return results


@router.post("/trigger-etl")
@limiter.limit("1/minute")
def trigger_etl(request: Request, current_user: User = Depends(require_role("admin"))):
    try:
        task = run_etl_pipeline_task.delay()
        return {
            "message": "ETL pipeline triggered successfully",
            "task_id": task.id,
            "status": "PENDING",
        }
    except Exception as e:
        import traceback
        error_details = f"Failed to trigger ETL: {str(e)}\nTraceback: {traceback.format_exc()}"
        print(f"ETL Error: {error_details}")  # Log to console
        raise HTTPException(status_code=500, detail=f"Failed to trigger ETL: {str(e)}")


@router.get("/task-status/{task_id}")
def get_task_status(task_id: str):
    try:
        task_result = celery_app.AsyncResult(task_id)

        # Get the current state info for progress tracking
        current_info = None
        if task_result.state == "PROGRESS":
            # For progress state, get the current meta information
            current_info = task_result.info
        elif task_result.ready():
            # For completed tasks, get the final result
            current_info = task_result.result

        return {
            "task_id": task_id,
            "status": task_result.status,
            "result": current_info,
            "info": task_result.info if hasattr(task_result, "info") else None,
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to get task status: {str(e)}"
        )


@router.post("/trigger-fetch")
@limiter.limit("5/minute")
def trigger_fetch(request: Request):
    try:
        task = fetch_nvd_feed_task.delay()
        return {
            "message": "Fetch triggered successfully",
            "task_id": task.id,
            "status": "PENDING",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger fetch: {str(e)}"
        )


@router.post("/trigger-transform")
@limiter.limit("5/minute")
def trigger_transform(request: Request):
    try:
        task = transform_and_load_task.delay()
        return {
            "message": "Transform and load triggered successfully",
            "task_id": task.id,
            "status": "PENDING",
        }
    except Exception as e:
        raise HTTPException(
            status_code=500, detail=f"Failed to trigger transform: {str(e)}"
        )
