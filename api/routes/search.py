from fastapi import APIRouter, Query
import psycopg2.extras
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database.db import get_connection
from api.schemas import CertificateListResponse

router = APIRouter(prefix="/search", tags=["Search"])


@router.get("", response_model=list[CertificateListResponse], summary="Qidiruv")
def search_certificates(
    q: str = Query(..., min_length=2, description="Qidiruv so'zi (tashkilot nomi, manzil, standart)"),
    limit: int = Query(20, ge=1, le=100),
):
    """
    Tashkilot nomi, manzil yoki standart bo'yicha erkin qidiruv.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT id, accreditation_number, country, organization_name, address,
                  standard, initial_date, expiry_date, status,
                  scope_url, source_url, created_at, updated_at
           FROM certificates
           WHERE organization_name ILIKE %s
              OR address           ILIKE %s
              OR standard          ILIKE %s
              OR accreditation_number ILIKE %s
           ORDER BY country, organization_name
           LIMIT %s""",
        (f"%{q}%", f"%{q}%", f"%{q}%", f"%{q}%", limit),
    )
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows

