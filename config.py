import os
from dotenv import load_dotenv

load_dotenv()

# ── PostgreSQL ────────────────────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_NAME     = os.getenv("DB_NAME", "halal_certificates")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ── HAK sayt URL lari ─────────────────────────────────────────────────────────
# Barcha akkreditatsiya ro'yxati (asosiy sahifa)
HAK_LIST_URL = os.getenv(
    "HAK_LIST_URL",
    "https://english.hak.gov.tr/accredited-hcabs"
)

# ── Fayl saqlash joyi ─────────────────────────────────────────────────────────
DOWNLOAD_DIR = os.getenv("DOWNLOAD_DIR", "halal_files")

# ── Crawler sozlamalari ───────────────────────────────────────────────────────
DELAY = float(os.getenv("REQUEST_DELAY", "1.5"))

HEADERS = {
    "User-Agent": (
        "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) "
        "AppleWebKit/537.36 (KHTML, like Gecko) "
        "Chrome/124.0.0.0 Safari/537.36"
    ),
    "Accept":          "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
    "Accept-Language": "tr-TR,tr;q=0.9,en;q=0.8",
    "Referer":         "https://english.hak.gov.tr/",
}
