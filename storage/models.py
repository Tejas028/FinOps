from pydantic import BaseModel

class UpsertResult(BaseModel):
    inserted: int
    skipped: int
    total: int
    duration_seconds: float
