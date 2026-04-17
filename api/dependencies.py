from fastapi import Depends, Query
from storage.db import DatabaseManager
import os

_db: DatabaseManager = None

def get_db() -> DatabaseManager:
    """
    Returns a module-level singleton DatabaseManager.
    """
    global _db
    if _db is None:
        # DB Manager handles its own initialization on first call to get_connection
        # but we can explicitly initialize if needed.
        # It reads from env, which api/config.py also uses.
        _db = DatabaseManager
    return _db

class PaginationParams:
    """
    Reusable pagination — inject with Depends(PaginationParams).
    Defaults: page=1, page_size=50, max page_size=500.
    """
    def __init__(
        self,
        page:      int = Query(default=1, ge=1),
        page_size: int = Query(default=50, ge=1, le=500)
    ):
        self.page      = page
        self.page_size = page_size
        self.offset    = (page - 1) * page_size
