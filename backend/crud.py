from sqlmodel import Session
from sqlalchemy.dialects.postgresql import insert
from backend.models import CVEItem
import itertools


def batched(iterable, n):
    "Batch data into tuples of length n. The last batch may be shorter."
    # batched('ABCDEFG', 3) --> ABC DEF G
    if n < 1:
        raise ValueError("n must be at least one")
    it = iter(iterable)
    while batch := tuple(itertools.islice(it, n)):
        yield batch


def upsert_cve_items(session: Session, cve_items):
    if not cve_items:
        print("No items to upsert.")
        return

    # Use Pydantic 2's proper serialization - Generator Expression for lazy evaluation
    values = (item.model_dump(exclude={"id"}, mode="json") for item in cve_items)

    for batch in batched(values, 1000):
        stmt = insert(CVEItem).values(list(batch))
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
        print("Upserted batch of 1000 items.")
