from fastapi import APIRouter, HTTPException, Query
from typing import Optional
import psycopg2
import psycopg2.extras
import sys
import os

sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.dirname(__file__))))
from database.db import get_connection
from api.schemas import CertificateResponse, CertificateListResponse, PaginatedResponse

router = APIRouter(prefix="/certificates", tags=["Certificates"])


def _row_to_dict(row) -> dict:
    return dict(row)


@router.get("", response_model=PaginatedResponse, summary="Barcha sertifikatlar")
def get_certificates(
    page: int = Query(1, ge=1, description="Sahifa raqami"),
    page_size: int = Query(20, ge=1, le=100, description="Har sahifada nechta"),
    country: Optional[str] = Query(None, description="Davlat bo'yicha filter"),
    status: Optional[str] = Query(None, description="Status: active | withdrawn | suspended"),
    standard: Optional[str] = Query(None, description="Standart bo'yicha filter"),
):
    """
    Barcha sertifikatlar ro'yxati. Pagination, country, status, standard bo'yicha filter qilish mumkin.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    filters = []
    params = []

    if country:
        filters.append("country ILIKE %s")
        params.append(f"%{country}%")
    if status:
        filters.append("status = %s")
        params.append(status.lower())
    if standard:
        filters.append("standard ILIKE %s")
        params.append(f"%{standard}%")

    where = ("WHERE " + " AND ".join(filters)) if filters else ""

    cur.execute(f"SELECT COUNT(*) as cnt FROM certificates {where}", params)
    total = cur.fetchone()["cnt"]

    offset = (page - 1) * page_size
    cur.execute(
        f"""SELECT id, accreditation_number, country, organization_name, address,
                   standard, initial_date, expiry_date, status,
                   scope_url, source_url, created_at, updated_at
            FROM certificates {where}
            ORDER BY country, accreditation_number
            LIMIT %s OFFSET %s""",
        params + [page_size, offset],
    )
    rows = [_row_to_dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()

    import math
    return {
        "total": total,
        "page": page,
        "page_size": page_size,
        "pages": math.ceil(total / page_size) if total else 0,
        "data": rows,
    }


@router.get("/expiring", response_model=list[CertificateListResponse], summary="Muddati tugayotgan sertifikatlar")
def get_expiring_certificates(
    days: int = Query(30, ge=1, le=365, description="Necha kun ichida tugaydi"),
):
    """
    Muddati yaqin tugaydigan sertifikatlar ro'yxati.
    Sana formati DD/MM/YYYY ko'rinishida saqlanganini hisobga oladi.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute(
        """SELECT id, accreditation_number, country, organization_name, address,
                  standard, initial_date, expiry_date, status,
                  scope_url, source_url, created_at, updated_at
           FROM certificates
           WHERE status = 'active'
             AND TO_DATE(expiry_date, 'DD/MM/YYYY') BETWEEN NOW() AND NOW() + INTERVAL '%s days'
           ORDER BY expiry_date""",
        (days,),
    )
    rows = [_row_to_dict(r) for r in cur.fetchall()]
    cur.close()
    conn.close()
    return rows


@router.get("/{acc_number}", response_model=CertificateResponse, summary="Akkreditatsiya raqami bo'yicha")
def get_certificate_by_acc(
    acc_number: str,
    country: Optional[str] = Query(None, description="Bir xil raqam bo'lsa davlatni ham bering"),
):
    """
    Akkreditatsiya raqami bo'yicha sertifikat va uning scope items larini qaytaradi.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if country:
        cur.execute(
            "SELECT * FROM certificates WHERE accreditation_number = %s AND country ILIKE %s",
            (acc_number, f"%{country}%"),
        )
    else:
        cur.execute(
            "SELECT * FROM certificates WHERE accreditation_number = %s",
            (acc_number,),
        )

    cert = cur.fetchone()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Sertifikat topilmadi: {acc_number}")

    cert = _row_to_dict(cert)

    cur.execute("SELECT * FROM scope_items WHERE certificate_id = %s", (cert["id"],))
    cert["scope_items"] = [_row_to_dict(r) for r in cur.fetchall()]

    cur.close()
    conn.close()
    return cert


@router.get("/id/{cert_id}", response_model=CertificateResponse, summary="ID bo'yicha sertifikat")
def get_certificate_by_id(cert_id: int):
    """
    Bazadagi ID bo'yicha sertifikat va uning scope items larini qaytaradi.
    """
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
    cur.execute("SELECT * FROM certificates WHERE id = %s", (cert_id,))
    cert = cur.fetchone()
    if not cert:
        raise HTTPException(status_code=404, detail=f"Sertifikat topilmadi: id={cert_id}")

    cert = _row_to_dict(cert)
    cur.execute("SELECT * FROM scope_items WHERE certificate_id = %s", (cert["id"],))
    cert["scope_items"] = [_row_to_dict(r) for r in cur.fetchall()]

    cur.close()
    conn.close()
    return cert

