from pydantic import BaseModel
from typing import List, Optional
from sqlalchemy.dialects.postgresql import JSONB
from sqlmodel import Column, SQLModel, Field


class CVEReference(SQLModel):
    url: str
    source: Optional[str] = None


class CVEItem(SQLModel, table=True):
    __tablename__ = "cve_items"  # type: ignore
    id: Optional[int] = Field(default=None, primary_key=True)
    cve_id: str = Field(index=True, unique=True)
    description: str
    published_date: str
    last_modified_date: str
    cvss_v3_score: Optional[float] = None
    severity: Optional[str] = None
    references: Optional[List[CVEReference]] = Field(sa_column=Column(JSONB))
    raw_data: dict = Field(sa_column=Column(JSONB))


class CVEPage(BaseModel):
    items: List[CVEItem]
    total: int
    skip: int
    limit: int
