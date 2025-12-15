import io
import os
import gzip
import json
import time
import logging
import requests
import ijson
import itertools
from datetime import datetime
from typing import Any, Generator
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


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch


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
        response = requests.get(NVD_RECENT_FEED_URL, timeout=60, stream=True)
        response.raise_for_status()

        # Save locally but we can also stream processing if we didn't need to file-save
        # For simplicity, we keep the file-save step but use stream=True for memory efficiency
        with open("nvd_recent_feed.json", "wb") as f:
            for chunk in response.iter_content(chunk_size=8192):
                f.write(chunk)

        feed_size = os.path.getsize("nvd_recent_feed.json")
        metrics["feed_size_bytes"] = feed_size
        logger.info(f"Downloaded {feed_size} bytes from NVD feed")

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


def parse_cve_items() -> Generator[CVEItem, None, None]:
    """
    Yield parsed CVE items from the downloaded feed using streaming.
    Returns generator of validated CVEItem objects.
    """
    # Note: We rely on the file existing from the fetch stage
    try:
        logger.info("Starting CVE streaming parse...")
        with open("nvd_recent_feed.json", "rb") as f:
            # Check if file is gzipped based on magic number or extension,
            # but usually fetch saves as raw JSON if url ends in .json
            # For robustness, we assume the file saved is standard JSON

            # Use ijson top-level streaming
            # Access the 'CVE_Items' array and iterate
            parser = ijson.items(f, "CVE_Items.item")

            for i, item in enumerate(parser):
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
                    yield validated

                except Exception as e:
                    logger.warning(f"Error parsing item {i}: {e}")
                    # We continue to next item

    except Exception as e:
        error_msg = f"Failed to parse CVE items stream: {e}"
        logger.error(error_msg)
        raise Exception(error_msg)


def transform_and_load() -> dict[str, Any]:
    """
    Transform and load CVE items into the database and ES in batches.
    Returns metrics about the operation.
    """
    start_time = time.time()
    metrics = {
        "start_time": datetime.now().isoformat(),
        "status": "success",
        "error": None,
        "items_processed": 0,
        "duration_seconds": 0,
    }

    try:
        logger.info("Starting CVE transformation and loading (Streaming Mode)...")
        cve_gen = parse_cve_items()

        total_processed = 0
        total_es_success = 0

        # Batching logic: Consume generator in chunks of 1000
        # This solves the Memory Issue by never holding full list
        for batch in batched(cve_gen, 1000):
            batch_list = list(batch)  # Convert tuple to list for downstream tools
            if not batch_list:
                continue

            # Load to Postgres
            with get_context_session() as session:
                upsert_cve_items(session, batch_list)

            # Index in Elasticsearch
            es_metrics = bulk_index_cve_items(batch_list)
            total_es_success += es_metrics.get("success_count", 0)

            total_processed += len(batch_list)
            logger.info(
                f"Processed batch of size {len(batch_list)}. Total: {total_processed}"
            )

        metrics["items_processed"] = total_processed
        metrics["elasticsearch_success"] = total_es_success

        duration = time.time() - start_time
        metrics["duration_seconds"] = duration
        logger.info(
            f"Successfully streaming loaded {total_processed} CVE entries in {duration:.2f} seconds"
        )

    except Exception as e:
        error_msg = f"Failed to transform and load CVE items: {e}"
        logger.error(error_msg)
        metrics["status"] = "error"
        metrics["error"] = str(e)
        raise Exception(error_msg)
    finally:
        # Cleanup
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
