import io
import os
import gzip
import json
import time
import logging
import requests
from datetime import datetime
from typing import Any
from dotenv import load_dotenv
from backend.models import CVEItem, CVEReference
from backend.elasticsearch_config import bulk_index_cve_items, create_cve_index
from backend.db import get_context_session
from backend.crud import upsert_cve_items

load_dotenv()
NVD_RECENT_FEED_URL = os.getenv("NVD_RECENT_FEED_URL", "")

# Configure logging
logger = logging.getLogger("etl")
logger.setLevel(logging.INFO)

# Create console handler if not exists
if not logger.handlers:
    handler = logging.StreamHandler()
    formatter = logging.Formatter(
        "%(asctime)s - %(name)s - %(levelname)s - %(message)s"
    )
    handler.setFormatter(formatter)
    logger.addHandler(handler)


def fetch_and_save_feed() -> dict[str, Any]:
    """
    Fetch NVD feed and save to local file.
    Returns metrics about the operation.
    """
    if not NVD_RECENT_FEED_URL:
        raise ValueError("NVD_RECENT_FEED_URL environment variable is required")
    start_time = time.time()
    metrics = {
        "start_time": datetime.now().isoformat(),
        "status": "success",
        "error": None,
        "feed_size_bytes": 0,
        "duration_seconds": 0,
    }

    try:
        logger.info("Starting NVD feed download...")
        response = requests.get(NVD_RECENT_FEED_URL, timeout=60)
        response.raise_for_status()

        feed_size = len(response.content)
        metrics["feed_size_bytes"] = feed_size
        logger.info(f"Downloaded {feed_size} bytes from NVD feed")

        with gzip.open(io.BytesIO(response.content), "rt", encoding="utf-8") as f:
            data = json.load(f)

        # Save locally as JSON
        with open("nvd_recent_feed.json", "w", encoding="utf-8") as out_file:
            json.dump(data, out_file, indent=2)

        duration = time.time() - start_time
        metrics["duration_seconds"] = duration
        logger.info(f"Feed downloaded and saved successfully in {duration:.2f} seconds")

    except requests.RequestException as e:
        error_msg = f"Failed to download NVD feed: {e}"
        logger.error(error_msg)
        metrics["status"] = "error"
        metrics["error"] = str(e)
        raise Exception(error_msg)
    except Exception as e:
        error_msg = f"Unexpected error during feed download: {e}"
        logger.error(error_msg)
        metrics["status"] = "error"
        metrics["error"] = str(e)
        raise Exception(error_msg)

    return metrics


def parse_cve_items() -> list[CVEItem]:
    """
    Parse CVE items from the downloaded feed.
    Returns list of validated CVEItem objects.
    """
    start_time = time.time()
    cve_items = []
    parse_errors = 0

    try:
        logger.info("Starting CVE parsing...")
        with open("nvd_recent_feed.json", encoding="utf-8") as f:
            feed_data = json.load(f)

        total_items = len(feed_data.get("CVE_Items", []))
        logger.info(f"Found {total_items} CVE items to parse")

        for i, item in enumerate(feed_data.get("CVE_Items", []), 1):
            try:
                cve_id = item["cve"]["CVE_data_meta"]["ID"]
                description_data = item["cve"]["description"]["description_data"]
                description = (
                    description_data[0]["value"]
                    if description_data
                    else "No description"
                )

                published_date = item.get("publishedDate", "")
                last_modified_date = item.get("lastModifiedDate", "")

                # Handle CVSS (optional)
                metrics = item.get("impact", {}).get("baseMetricV3", {})
                cvss_v3_score = None
                severity = None
                if metrics:
                    cvss_v3_score = metrics.get("cvssV3", {}).get("baseScore")
                    severity = metrics.get("cvssV3", {}).get("baseSeverity")

                # References
                refs = []
                for ref in item["cve"]["references"]["reference_data"]:
                    refs.append(
                        CVEReference(url=ref["url"], source=ref.get("refsource"))
                    )

                validated = CVEItem(
                    cve_id=cve_id,
                    description=description,
                    published_date=published_date,
                    last_modified_date=last_modified_date,
                    cvss_v3_score=cvss_v3_score,
                    severity=severity,
                    references=refs,
                    raw_data=item,
                )
                cve_items.append(validated)

            except Exception as e:
                parse_errors += 1
                logger.warning(f"Error parsing CVE item {i}: {e}")

        duration = time.time() - start_time
        logger.info(
            f"Parsing completed: {len(cve_items)} successful, {parse_errors} errors in {duration:.2f} seconds"
        )

        if parse_errors > 0:
            logger.warning(
                f"Parse error rate: {parse_errors}/{total_items} ({parse_errors/total_items*100:.1f}%)"
            )

    except Exception as e:
        error_msg = f"Failed to parse CVE items: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)

    return cve_items


def transform_and_load() -> dict[str, Any]:
    """
    Transform and load CVE items into the database.
    Returns metrics about the operation.
    """
    start_time = time.time()
    metrics = {
        "start_time": datetime.now().isoformat(),
        "status": "success",
        "error": None,
        "items_processed": 0,
        "items_updated": 0,
        "items_inserted": 0,
        "duration_seconds": 0,
    }

    try:
        logger.info("Starting CVE transformation and loading...")
        cve_items = parse_cve_items()

        if not cve_items:
            logger.warning("No CVE items to process")
            return metrics

        metrics["items_processed"] = len(cve_items)
        logger.info(f"Processing {len(cve_items)} CVE items for database insertion")

        with get_context_session() as session:
            # Note: You might want to enhance crud.upsert_cve_items to return detailed metrics
            upsert_cve_items(session, cve_items)

        # Index in Elasticsearch
        logger.info("Indexing CVE items in Elasticsearch...")
        es_metrics = bulk_index_cve_items(cve_items)
        metrics["elasticsearch"] = es_metrics
        logger.info(
            f"Elasticsearch indexing: {es_metrics['success_count']} successful, {es_metrics['error_count']} errors"
        )

        duration = time.time() - start_time
        metrics["duration_seconds"] = duration
        logger.info(
            f"Successfully loaded {len(cve_items)} CVE entries in {duration:.2f} seconds"
        )

    except Exception as e:
        error_msg = f"Failed to transform and load CVE items: {e}"
        logger.error(error_msg)
        metrics["status"] = "error"
        metrics["error"] = str(e)
        raise Exception(error_msg)
    finally:
        # Cleanup: Remove the temporary feed file
        try:
            if os.path.exists("nvd_recent_feed.json"):
                os.remove("nvd_recent_feed.json")
                logger.info("Cleaned up temporary feed file")
        except Exception as e:
            logger.warning(f"Failed to cleanup feed file: {e}")

    return metrics


def run_etl_pipeline(triggered_by: str = "manual") -> dict[str, Any]:
    """
    Run the complete ETL pipeline with comprehensive monitoring.
    Returns overall pipeline metrics.
    """
    pipeline_start = time.time()
    pipeline_metrics = {
        "pipeline_start": datetime.now().isoformat(),
        "status": "success",
        "error": None,
        "stages": {},
        "total_duration_seconds": 0,
    }

    try:
        logger.info("Starting ETL pipeline...")

        # Stage 1: Fetch
        logger.info("=== STAGE 1: FETCH ===")
        fetch_metrics = fetch_and_save_feed()
        pipeline_metrics["stages"]["fetch"] = fetch_metrics

        # Stage 2: Transform and Load
        logger.info("=== STAGE 2: TRANSFORM AND LOAD ===")
        load_metrics = transform_and_load()
        pipeline_metrics["stages"]["load"] = load_metrics

        # Stage 3: Setup Elasticsearch (if needed)
        logger.info("=== STAGE 3: ELASTICSEARCH SETUP ===")
        create_cve_index()

        total_duration = time.time() - pipeline_start
        pipeline_metrics["total_duration_seconds"] = total_duration
        pipeline_metrics["pipeline_end"] = datetime.now().isoformat()

        logger.info(
            f"ETL pipeline completed successfully in {total_duration:.2f} seconds"
        )

    except Exception as e:
        error_msg = f"ETL pipeline failed: {e}"
        logger.error(error_msg)
        pipeline_metrics["status"] = "error"
        pipeline_metrics["error"] = str(e)
        pipeline_metrics["pipeline_end"] = datetime.now().isoformat()
        raise Exception(error_msg) from e

    return pipeline_metrics
