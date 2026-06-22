import os
from dotenv import load_dotenv

load_dotenv()

# ── PostgreSQL ────────────────────────────────────────────────────────────────
DB_HOST     = os.getenv("DB_HOST", "localhost")
DB_PORT     = int(os.getenv("DB_PORT", "5432"))
DB_NAME     = os.getenv("DB_NAME", "halal_certificates")
DB_USER     = os.getenv("DB_USER", "postgres")
DB_PASSWORD = os.getenv("DB_PASSWORD", "")

# ── Autentifikatsiya (JWT) ───────────────────────────────────────────────────
# .env faylga albatta o'zingiz SECRET_KEY qo'shing! Quyidagi buyruq bilan
# tasodifiy kalit generatsiya qilishingiz mumkin:
#   python -c "import secrets; print(secrets.token_hex(32))"
SECRET_KEY = os.getenv("SECRET_KEY", "")
if not SECRET_KEY:
    raise RuntimeError(
        "SECRET_KEY .env faylda topilmadi. "
        'Generatsiya qilish uchun: python -c "import secrets; print(secrets.token_hex(32))"'
    )

ALGORITHM = "HS256"
ACCESS_TOKEN_EXPIRE_MINUTES = int(os.getenv("ACCESS_TOKEN_EXPIRE_MINUTES", "480"))  # 8 soat

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

