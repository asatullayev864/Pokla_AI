from fastapi import APIRouter, HTTPException
import psycopg2.extras
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database.db import get_connection
from api.schemas import CountryStats, SummaryStats

router = APIRouter(prefix="/countries", tags=["Countries"])


@router.get("", response_model=list[CountryStats], summary="Barcha davlatlar statistikasi")
def get_countries():
    """
    Barcha davlatlar va ularning sertifikat statistikasi.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM countries ORDER BY total_certificates DESC")
    rows = [dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


@router.get("/summary", response_model=SummaryStats, summary="Umumiy statistika")
def get_summary():
    """
    Jami davlatlar, sertifikatlar va statuslar bo'yicha umumiy statistika.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("""
        SELECT
            COUNT(DISTINCT country)                                              AS total_countries,
            COUNT(*)                                                             AS total_certificates,
            COUNT(*) FILTER (WHERE status = 'active')                           AS active_certificates,
            COUNT(*) FILTER (WHERE status = 'withdrawn')                        AS withdrawn_certificates,
            COUNT(*) FILTER (WHERE status = 'suspended')                        AS suspended_certificates
        FROM certificates
    """)
    row = dict(cur.fetchone())
    cur.close()
    conn.close()
    return row


@router.get("/{country}", response_model=CountryStats, summary="Bitta davlat statistikasi")
def get_country_stats(country: str):
    """
    Bitta davlat uchun batafsil statistika.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM countries WHERE country ILIKE %s", (f"%{country}%",))
    row = cur.fetchone()
    if not row:
        raise HTTPException(status_code=404, detail=f"Davlat topilmadi: {country}")
    cur.close()
    conn.close()
    return dict(row)

