import os
import re
import time
import logging
import hashlib
import requests
from urllib.parse import urljoin, urlparse
from bs4 import BeautifulSoup

from config import HEADERS, DELAY, DOWNLOAD_DIR
from parser.html_parser import parse_certificate
from database.db import upsert_certificate, log_crawl

log = logging.getLogger(__name__)


def fetch_html(url: str) -> str | None:
    """URL dan HTML yuklab oladi."""
    try:
        r = requests.get(url, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
        return r.text
    except Exception as e:
        log.error("❌  Yuklab bo'lmadi %s : %s", url, e)
        return None


def download_pdf(url: str, country: str = "") -> str | None:
    """PDF faylni DOWNLOAD_DIR/<country>/ ga saqlaydi."""
    save_dir = os.path.join(DOWNLOAD_DIR, country) if country else DOWNLOAD_DIR
    os.makedirs(save_dir, exist_ok=True)
    try:
        r = requests.get(url, headers=HEADERS, timeout=60, stream=True)
        r.raise_for_status()
    except Exception as e:
        log.error("❌  PDF yuklab bo'lmadi %s : %s", url, e)
        return None

    parsed = urlparse(url)
    fname  = os.path.basename(parsed.path) or "cert.pdf"
    uid    = hashlib.md5(url.encode()).hexdigest()[:6]
    name, ext = os.path.splitext(fname)
    fpath  = os.path.join(save_dir, f"{name}_{uid}{ext}")

    if os.path.exists(fpath):
        log.info("⏩  Allaqachon bor: %s", fpath)
        return fpath

    with open(fpath, "wb") as f:
        for chunk in r.iter_content(64 * 1024):
            f.write(chunk)
    log.info("⬇️   PDF saqlandi: %s", fpath)
    return fpath


def run_for_country(country: str, entries: list[dict]):
    """
    Bitta davlat uchun barcha sertifikatlarni qayta ishlaydi.

    entries — hak_directory.py dan kelgan ro'yxat, har birida:
        accreditation_number, organization_name, location,
        initial_date, expiry_date, status,
        scope_html_url, scope_pdf_url
    """
    log.info("\n%s", "=" * 60)
    log.info("🌍  Davlat: %s  (%d ta sertifikat)", country, len(entries))
    log.info("=" * 60)

    for entry in entries:
        acc        = entry.get("accreditation_number", "?")
        scope_html = entry.get("scope_html_url", "")
        scope_pdf  = entry.get("scope_pdf_url", "")

        log.info("\n📜  [%s] %s", acc, entry.get("organization_name", ""))

        # ── 1. Scope HTML dan to'liq ma'lumot olish ─────────────
        scope_items = []
        standard    = None
        address     = entry.get("location", "")

        if scope_html:
            log.info("   🌐  Scope HTML: %s", scope_html)
            html = fetch_html(scope_html)
            if html:
                parsed = parse_certificate(html, source_url=scope_html)
                scope_items = parsed.get("scope_items", [])
                standard    = parsed.get("standard")
                if parsed.get("address"):
                    address = parsed["address"]
            else:
                log_crawl(scope_html, "error", "fetch failed", country=country)
            time.sleep(DELAY)

        # ── 2. PDF ni yuklab saqlash ─────────────────────────────
        if scope_pdf:
            log.info("   📄  PDF yuklanmoqda: %s", scope_pdf)
            fpath = download_pdf(scope_pdf, country=country)
            if not fpath:
                log_crawl(scope_pdf, "error", "pdf download failed", country=country)
            else:
                log_crawl(scope_pdf, "ok", f"saved: {fpath}", country=country)
            time.sleep(DELAY)

        # ── 3. Bazaga yozish ─────────────────────────────────────
        cert = {
            "accreditation_number": acc,
            "country":              country,
            "organization_name":    entry.get("organization_name"),
            "address":              address,
            "standard":             standard,
            "initial_date":         entry.get("initial_date"),
            "expiry_date":          entry.get("expiry_date"),
            "status":               entry.get("status", "active"),
            "scope_url":            scope_html or scope_pdf,
            "source_url":           scope_html,
            "scope_items":          scope_items,
        }
        cert_id = upsert_certificate(cert)

        status_str = "ok" if cert_id else "no_data"
        log_crawl(scope_html or scope_pdf or acc, status_str, country=country)

    log.info("\n✅  [%s] tugadi.", country)
