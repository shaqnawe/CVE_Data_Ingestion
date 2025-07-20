from fastapi import APIRouter, Depends, HTTPException, Query
from typing import Optional
from models import User
from auth import get_current_active_user
from elasticsearch_config import search_cves, get_index_stats, delete_cve_index

router = APIRouter(prefix="/elasticsearch", tags=["elasticsearch"])


@router.get("/search")
async def search_cve_elasticsearch(
    query: str = Query(..., description="Search query"),
    severity: Optional[str] = Query(None, description="Filter by severity (HIGH, MEDIUM, LOW)"),
    min_cvss_score: Optional[float] = Query(None, description="Minimum CVSS score"),
    max_cvss_score: Optional[float] = Query(None, description="Maximum CVSS score"),
    from_date: Optional[str] = Query(None, description="From date (YYYY-MM-DD)"),
    to_date: Optional[str] = Query(None, description="To date (YYYY-MM-DD)"),
    size: int = Query(10, description="Number of results to return"),
    from_: int = Query(0, alias="from", description="Starting offset"),
    current_user: User = Depends(get_current_active_user)
):
    """Search CVEs using Elasticsearch with advanced filtering."""
    try:
        results = search_cves(
            query=query,
            severity=severity,
            min_cvss_score=min_cvss_score,
            max_cvss_score=max_cvss_score,
            from_date=from_date,
            to_date=to_date,
            size=size,
            from_=from_
        )
        
        return {
            "query": query,
            "filters": {
                "severity": severity,
                "min_cvss_score": min_cvss_score,
                "max_cvss_score": max_cvss_score,
                "from_date": from_date,
                "to_date": to_date
            },
            "results": results["results"],
            "total": results["total"],
            "took": results["took"],
            "pagination": {
                "size": size,
                "from": from_,
                "total_pages": (results["total"] + size - 1) // size
            }
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Search failed: {str(e)}")


@router.get("/stats")
async def get_elasticsearch_stats(
    current_user: User = Depends(get_current_active_user)
):
    """Get Elasticsearch index statistics."""
    try:
        stats = get_index_stats()
        return {
            "index_name": "cve_items",
            "document_count": stats["document_count"],
            "index_size_bytes": stats["index_size"],
            "index_size_mb": round(stats["index_size"] / (1024 * 1024), 2)
        }
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to get stats: {str(e)}")


@router.delete("/index")
async def delete_elasticsearch_index(
    current_user: User = Depends(get_current_active_user)
):
    """Delete the Elasticsearch index (admin only)."""
    if current_user.role.value != "admin":
        raise HTTPException(status_code=403, detail="Admin access required")
    
    try:
        delete_cve_index()
        return {"message": "Elasticsearch index deleted successfully"}
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Failed to delete index: {str(e)}") 