import logging
import psycopg2
import psycopg2.extras
from config import DB_HOST, DB_PORT, DB_NAME, DB_USER, DB_PASSWORD

log = logging.getLogger(__name__)


def get_connection():
    return psycopg2.connect(
        host=DB_HOST,
        port=DB_PORT,
        dbname=DB_NAME,
        user=DB_USER,
        password=DB_PASSWORD
    )


def init_db():
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("""
        CREATE TABLE IF NOT EXISTS certificates (
            id                   SERIAL PRIMARY KEY,
            accreditation_number TEXT    NOT NULL,
            country              TEXT    NOT NULL,
            organization_name    TEXT,
            address              TEXT,
            standard             TEXT,
            initial_date         TEXT,
            expiry_date          TEXT,
            status               TEXT    DEFAULT 'active',
            scope_url            TEXT,
            source_url           TEXT,
            created_at           TIMESTAMP DEFAULT NOW(),
            updated_at           TIMESTAMP DEFAULT NOW(),
            UNIQUE (accreditation_number, country)
        );

        CREATE TABLE IF NOT EXISTS scope_items (
            id               SERIAL PRIMARY KEY,
            certificate_id   INTEGER NOT NULL REFERENCES certificates(id) ON DELETE CASCADE,
            cluster          TEXT,
            category_code    TEXT,
            category_name    TEXT,
            subcategory_code TEXT,
            subcategory_name TEXT,
            activities       TEXT
        );

        CREATE TABLE IF NOT EXISTS crawl_log (
            id         SERIAL PRIMARY KEY,
            country    TEXT,
            url        TEXT,
            status     TEXT,
            note       TEXT,
            crawled_at TIMESTAMP DEFAULT NOW()
        );

        CREATE TABLE IF NOT EXISTS countries (
            id                     SERIAL PRIMARY KEY,
            country                TEXT NOT NULL UNIQUE,
            total_certificates     INTEGER DEFAULT 0,
            active_certificates    INTEGER DEFAULT 0,
            withdrawn_certificates INTEGER DEFAULT 0,
            suspended_certificates INTEGER DEFAULT 0,
            first_cert_date        TEXT,
            latest_cert_date       TEXT,
            created_at             TIMESTAMP DEFAULT NOW(),
            updated_at             TIMESTAMP DEFAULT NOW()
        );
    """)
    conn.commit()
    cur.close()
    conn.close()
    log.info("✅  PostgreSQL jadvallar tayyor: %s:%s/%s", DB_HOST, DB_PORT, DB_NAME)


def update_country_stats(country: str, conn=None):
    """Davlat statistikasini certificates jadvalidan qayta hisoblaydi."""
    close_conn = False
    if conn is None:
        conn = get_connection()
        close_conn = True

    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO countries (
                country,
                total_certificates,
                active_certificates,
                withdrawn_certificates,
                suspended_certificates,
                first_cert_date,
                latest_cert_date,
                updated_at
            )
            SELECT
                country,
                COUNT(DISTINCT accreditation_number)                                          AS total_certificates,
                COUNT(DISTINCT CASE WHEN status = 'active'    THEN accreditation_number END) AS active_certificates,
                COUNT(DISTINCT CASE WHEN status = 'withdrawn' THEN accreditation_number END) AS withdrawn_certificates,
                COUNT(DISTINCT CASE WHEN status = 'suspended' THEN accreditation_number END) AS suspended_certificates,
                MIN(initial_date)                                                             AS first_cert_date,
                MAX(initial_date)                                                             AS latest_cert_date,
                NOW()
            FROM certificates
            WHERE country = %s
            GROUP BY country
            ON CONFLICT (country) DO UPDATE SET
                total_certificates     = EXCLUDED.total_certificates,
                active_certificates    = EXCLUDED.active_certificates,
                withdrawn_certificates = EXCLUDED.withdrawn_certificates,
                suspended_certificates = EXCLUDED.suspended_certificates,
                first_cert_date        = EXCLUDED.first_cert_date,
                latest_cert_date       = EXCLUDED.latest_cert_date,
                updated_at             = NOW()
        """, (country,))
        conn.commit()
        log.info("🌍  Countries yangilandi: %s", country)
    except Exception as e:
        conn.rollback()
        log.error("❌  Countries yangilashda xato: %s", e)
    finally:
        cur.close()
        if close_conn:
            conn.close()


def upsert_certificate(cert: dict) -> int | None:
    acc     = cert.get("accreditation_number")
    country = cert.get("country")

    if not acc:
        log.warning("⚠️  accreditation_number yo'q, o'tkazib yuborildi")
        return None
    if not country:
        log.warning("⚠️  country yo'q, o'tkazib yuborildi")
        return None

    conn = get_connection()
    cur = conn.cursor()
    try:
        cur.execute("""
            INSERT INTO certificates
                (accreditation_number, country, organization_name, address,
                 standard, initial_date, expiry_date, status, scope_url, source_url, updated_at)
            VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, NOW())
            ON CONFLICT (accreditation_number, country) DO UPDATE SET
                organization_name = EXCLUDED.organization_name,
                address           = EXCLUDED.address,
                standard          = EXCLUDED.standard,
                initial_date      = EXCLUDED.initial_date,
                expiry_date       = EXCLUDED.expiry_date,
                status            = EXCLUDED.status,
                scope_url         = EXCLUDED.scope_url,
                source_url        = EXCLUDED.source_url,
                updated_at        = NOW()
            RETURNING id
        """, (
            acc,
            country,
            cert.get("organization_name"),
            cert.get("address"),
            cert.get("standard"),
            cert.get("initial_date"),
            cert.get("expiry_date"),
            cert.get("status", "active"),
            cert.get("scope_url"),
            cert.get("source_url"),
        ))
        cert_id = cur.fetchone()[0]
        conn.commit()

        scope_items = cert.get("scope_items", [])
        if scope_items:
            cur.execute("DELETE FROM scope_items WHERE certificate_id = %s", (cert_id,))
            psycopg2.extras.execute_values(cur, """
                INSERT INTO scope_items
                    (certificate_id, cluster, category_code, category_name,
                     subcategory_code, subcategory_name, activities)
                VALUES %s
            """, [
                (
                    cert_id,
                    s.get("cluster"),
                    s.get("category_code"),
                    s.get("category_name"),
                    s.get("subcategory_code"),
                    s.get("subcategory_name"),
                    s.get("activities"),
                )
                for s in scope_items
            ])
            conn.commit()
            log.info("   📋  %d ta scope saqlandi", len(scope_items))

        log.info("💾  Saqlandi: [%s] %s  (id=%d)", country, acc, cert_id)

        # Countries jadvalini avtomatik yangilash
        update_country_stats(country, conn)

        return cert_id

    except Exception as e:
        conn.rollback()
        log.error("❌  Bazaga yozishda xato: %s", e)
        return None
    finally:
        cur.close()
        conn.close()


def log_crawl(url: str, status: str, note: str = "", country: str = ""):
    conn = get_connection()
    cur = conn.cursor()
    cur.execute(
        "INSERT INTO crawl_log (country, url, status, note) VALUES (%s, %s, %s, %s)",
        (country, url, status, note)
    )
    conn.commit()
    cur.close()
    conn.close()


def get_all_countries() -> list[str]:
    """Bazadagi barcha davlatlar ro'yxati."""
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT DISTINCT country FROM certificates ORDER BY country")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return [r[0] for r in rows]


def print_report(country: str = None):
    conn = get_connection()
    cur = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)

    if country:
        cur.execute(
            "SELECT * FROM certificates WHERE country = %s ORDER BY id",
            (country,)
        )
    else:
        cur.execute("SELECT * FROM certificates ORDER BY country, id")

    certs = cur.fetchall()

    print("\n" + "=" * 65)
    print("📊  NATIJALAR" + (f" — {country}" if country else " — Barcha davlatlar"))
    print("=" * 65)
    print(f"Jami sertifikatlar: {len(certs)}\n")

    current_country = None
    for c in certs:
        if not country and c["country"] != current_country:
            current_country = c["country"]
            print(f"\n🌍  {current_country}")
            print("  " + "-" * 55)

        print(f"  📜  Raqam      : {c['accreditation_number']}")
        print(f"       Tashkilot : {c['organization_name']}")
        print(f"       Manzil    : {c['address']}")
        print(f"       Standart  : {c['standard']}")
        print(f"       Status    : {c['status']}")
        print(f"       Boshlanish: {c['initial_date']}")
        print(f"       Tugash    : {c['expiry_date']}")
        print(f"       Scope URL : {c['scope_url']}")

        cur2 = conn.cursor(cursor_factory=psycopg2.extras.RealDictCursor)
        cur2.execute(
            "SELECT * FROM scope_items WHERE certificate_id = %s", (c["id"],)
        )
        scopes = cur2.fetchall()
        if scopes:
            print(f"       Scope ({len(scopes)} ta):")
            for s in scopes:
                print(f"         [{s['subcategory_code']}] {s['subcategory_name']}")
        print()

    print("=" * 65)
    cur.close()
    conn.close()

