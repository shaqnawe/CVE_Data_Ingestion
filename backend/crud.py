from sqlmodel import Session
from sqlalchemy.dialects.postgresql import insert
from backend.models import CVEItem


def upsert_cve_items(session: Session, cve_items):
    if not cve_items:
        print("No items to upsert.")
        return

    # Use Pydantic 2's proper serialization
    values = [item.model_dump(exclude={"id"}, mode="json") for item in cve_items]

    stmt = insert(CVEItem).values(values)
    stmt = stmt.on_conflict_do_update(
        index_elements=["cve_id"],
        set_={
            "description": stmt.excluded.description,
            "last_modified_date": stmt.excluded.last_modified_date,
            "cvss_v3_score": stmt.excluded.cvss_v3_score,
            "severity": stmt.excluded.severity,
            "references": stmt.excluded.references,
            "raw_data": stmt.excluded.raw_data,
        },
    )

    session.execute(stmt)
    session.commit()
