import os
from elasticsearch import Elasticsearch
from typing import List, Dict, Any
from models import CVEItem

# Elasticsearch configuration
ELASTICSEARCH_URL = os.getenv("ELASTICSEARCH_URL", "http://localhost:9200")
ELASTICSEARCH_INDEX = "cve_items"

# Initialize Elasticsearch client
es_client = Elasticsearch(
    [ELASTICSEARCH_URL], request_timeout=30, max_retries=3, retry_on_timeout=True
)


def test_elasticsearch_connection():
    """Test connection to Elasticsearch."""
    try:
        info = es_client.info()
        print(f"Connected to Elasticsearch: {info['version']['number']}")
        return True
    except Exception as e:
        print(f"Failed to connect to Elasticsearch: {e}")
        return False


def create_cve_index():
    """Create the CVE index with proper mappings."""
    index_mapping = {
        "mappings": {
            "properties": {
                "cve_id": {"type": "keyword"},
                "description": {"type": "text", "analyzer": "standard"},
                "published_date": {"type": "date"},
                "last_modified_date": {"type": "date"},
                "cvss_v3_score": {"type": "float"},
                "severity": {"type": "keyword"},
                "references": {
                    "type": "nested",
                    "properties": {
                        "url": {"type": "keyword"},
                        "source": {"type": "keyword"},
                    },
                },
                "raw_data": {"type": "object", "enabled": False},
            }
        },
        "settings": {"number_of_shards": 1, "number_of_replicas": 0},
    }

    try:
        if not es_client.indices.exists(index=ELASTICSEARCH_INDEX):
            es_client.indices.create(
                index=ELASTICSEARCH_INDEX,
                mappings=index_mapping["mappings"],
                settings=index_mapping["settings"],
            )
            print(f"Created Elasticsearch index: {ELASTICSEARCH_INDEX}")
        else:
            print(f"Elasticsearch index already exists: {ELASTICSEARCH_INDEX}")
    except Exception as e:
        print(f"Error creating Elasticsearch index: {e}")


def index_cve_item(cve_item: CVEItem) -> bool:
    """Index a single CVE item in Elasticsearch."""
    try:
        # Convert references to dict format for Elasticsearch
        references = []
        if cve_item.references:
            for ref in cve_item.references:
                references.append({"url": ref.url, "source": ref.source})

        # Handle date formatting
        published_date = cve_item.published_date
        last_modified_date = cve_item.last_modified_date

        # Convert to ISO format if needed
        if published_date and not published_date.endswith("Z"):
            published_date = published_date.replace("Z", "") + "Z"
        if last_modified_date and not last_modified_date.endswith("Z"):
            last_modified_date = last_modified_date.replace("Z", "") + "Z"

        doc = {
            "cve_id": cve_item.cve_id,
            "description": cve_item.description,
            "published_date": published_date,
            "last_modified_date": last_modified_date,
            "cvss_v3_score": cve_item.cvss_v3_score,
            "severity": cve_item.severity,
            "references": references,
            "raw_data": cve_item.raw_data,
        }

        es_client.index(index=ELASTICSEARCH_INDEX, id=cve_item.cve_id, document=doc)
        return True
    except Exception as e:
        print(f"Error indexing CVE {cve_item.cve_id}: {e}")
        return False


def bulk_index_cve_items(cve_items: List[CVEItem]) -> Dict[str, int]:
    """Bulk index multiple CVE items."""
    success_count = 0
    error_count = 0

    for cve_item in cve_items:
        if index_cve_item(cve_item):
            success_count += 1
        else:
            error_count += 1

    return {
        "success_count": success_count,
        "error_count": error_count,
        "total_count": len(cve_items),
    }


def search_cves(
    query: str,
    severity: str | None = None,
    min_cvss_score: float | None = None,
    max_cvss_score: float | None = None,
    from_date: str | None = None,
    to_date: str | None = None,
    size: int = 10,
    from_: int = 0,
) -> Dict[str, Any]:
    """Search CVEs using Elasticsearch."""
    search_body = {
        "query": {
            "bool": {
                "must": [
                    {
                        "multi_match": {
                            "query": query,
                            "fields": ["cve_id^2", "description"],
                            "type": "best_fields",
                            "fuzziness": "AUTO",
                        }
                    }
                ],
                "filter": [],
            }
        },
        "sort": [{"_score": {"order": "desc"}}, {"published_date": {"order": "desc"}}],
        "size": size,
        "from": from_,
    }

    # Add filters
    if severity:
        search_body["query"]["bool"]["filter"].append(
            {"term": {"severity": severity.upper()}}
        )

    if min_cvss_score is not None or max_cvss_score is not None:
        cvss_filter = {"range": {"cvss_v3_score": {}}}
        if min_cvss_score is not None:
            cvss_filter["range"]["cvss_v3_score"]["gte"] = min_cvss_score
        if max_cvss_score is not None:
            cvss_filter["range"]["cvss_v3_score"]["lte"] = max_cvss_score
        search_body["query"]["bool"]["filter"].append(cvss_filter)

    if from_date or to_date:
        date_filter = {"range": {"published_date": {}}}
        if from_date:
            date_filter["range"]["published_date"]["gte"] = from_date
        if to_date:
            date_filter["range"]["published_date"]["lte"] = to_date
        search_body["query"]["bool"]["filter"].append(date_filter)

    try:
        response = es_client.search(
            index=ELASTICSEARCH_INDEX,
            query=search_body["query"],
            sort=search_body["sort"],
            size=search_body["size"],
            from_=search_body["from"],
        )

        hits = response["hits"]["hits"]
        total = response["hits"]["total"]["value"]

        results = []
        for hit in hits:
            source = hit["_source"]
            results.append(
                {
                    "cve_id": source["cve_id"],
                    "description": source["description"],
                    "published_date": source["published_date"],
                    "last_modified_date": source["last_modified_date"],
                    "cvss_v3_score": source.get("cvss_v3_score"),
                    "severity": source.get("severity"),
                    "references": source.get("references", []),
                    "score": hit["_score"],
                }
            )

        return {"results": results, "total": total, "took": response["took"]}
    except Exception as e:
        print(f"Elasticsearch search error: {e}")
        return {"results": [], "total": 0, "took": 0, "error": str(e)}


def delete_cve_index():
    """Delete the CVE index."""
    try:
        if es_client.indices.exists(index=ELASTICSEARCH_INDEX):
            es_client.indices.delete(index=ELASTICSEARCH_INDEX)
            print(f"Deleted Elasticsearch index: {ELASTICSEARCH_INDEX}")
        else:
            print(f"Index does not exist: {ELASTICSEARCH_INDEX}")
    except Exception as e:
        print(f"Error deleting Elasticsearch index: {e}")


def get_index_stats():
    """Get statistics about the CVE index."""
    try:
        stats = es_client.indices.stats(index=ELASTICSEARCH_INDEX)
        return {
            "document_count": stats["indices"][ELASTICSEARCH_INDEX]["total"]["docs"][
                "count"
            ],
            "index_size": stats["indices"][ELASTICSEARCH_INDEX]["total"]["store"][
                "size_in_bytes"
            ],
        }
    except Exception as e:
        print(f"Error getting index stats: {e}")
        return {"document_count": 0, "index_size": 0}
