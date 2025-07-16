import io
import os
import gzip
import json
import requests
from db import get_context_session
from dotenv import load_dotenv
from crud import upsert_cve_items
from models import CVEItem, CVEReference

load_dotenv()
NVD_RECENT_FEED_URL = os.getenv("NVD_RECENT_FEED_URL", "")


def fetch_and_save_feed():
    print("Downloading NVD feed...")
    response = requests.get(NVD_RECENT_FEED_URL, timeout=60)
    response.raise_for_status()

    with gzip.open(io.BytesIO(response.content), "rt", encoding="utf-8") as f:
        data = json.load(f)

    # For now, just save locally as JSON
    with open("nvd_recent_feed.json", "w", encoding="utf-8") as out_file:
        json.dump(data, out_file, indent=2)

    print("Feed downloaded and saved.")


def parse_cve_items():
    with open("nvd_recent_feed.json", encoding="utf-8") as f:
        feed_data = json.load(f)

    cve_items = []
    for item in feed_data.get("CVE_Items", []):
        try:
            cve_id = item["cve"]["CVE_data_meta"]["ID"]
            description_data = item["cve"]["description"]["description_data"]
            description = (
                description_data[0]["value"] if description_data else "No description"
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
                refs.append(CVEReference(url=ref["url"], source=ref.get("refsource")))

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
            print(f"Error parsing CVE item: {e}")

    print(f"Parsed and validated {len(cve_items)} CVE entries.")
    return cve_items


def transform_and_load():
    cve_items = parse_cve_items()
    with get_context_session() as session:
        upsert_cve_items(session, cve_items)
    print(f"Loaded {len(cve_items)} CVE entries into the database.")
