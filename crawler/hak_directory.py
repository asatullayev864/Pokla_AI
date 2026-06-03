"""
HAK asosiy sahifasidan barcha davlatlar va ularning
scope HTML URL larini avtomatik topadi.

Qaytaradi:
    {
      "Uzbekistan": [
          {
            "accreditation_number": "2025-077",
            "organization_name":    "UzHalalTest",
            "scope_html_url":       "https://..../uztest.html",
            "scope_pdf_url":        "https://..../uztest.pdf",
            "initial_date":         "13/10/2025",
            "expiry_date":          "13/10/2030",
            "status":               "active",
          },
          ...
      ],
      "Azerbaijan": [...],
      ...
    }
"""

import re
import logging
import requests
from bs4 import BeautifulSoup

from config import HEADERS, HAK_LIST_URL

log = logging.getLogger(__name__)

COUNTRY_ALIASES: dict[str, str] = {
    "türkiye":                    "Türkiye",
    "turkey":                     "Türkiye",
    "uzbekistan":                 "Uzbekistan",
    "azerbaijan":                 "Azerbaijan",
    "russia":                     "Russia",
    "russian federation":         "Russia",
    "kazakhstan":                 "Kazakhstan",
    "kyrgyzstan":                 "Kyrgyzstan",
    "tajikistan":                 "Tajikistan",
    "turkmenistan":               "Turkmenistan",
    "united arab emirates":       "United Arab Emirates",
    "uae":                        "United Arab Emirates",
    "south korea":                "South Korea",
    "korea":                      "South Korea",
    "saudi arabia":               "Saudi Arabia",
    "kingdom of saudi arabia":    "Saudi Arabia",
    "the netherlands":            "Netherlands",
    "netherlands":                "Netherlands",
    "united kingdom":             "United Kingdom",
    "england":                    "United Kingdom",
    "great britain":              "United Kingdom",
    "brasil":                     "Brazil",
    "brazil":                     "Brazil",
    "south africa":               "South Africa",
    "state of palestine":         "Palestine",
    "palestine":                  "Palestine",
    "china":                      "China",
    "people's republic of china": "China",
}


def _normalize_country(raw: str) -> str:
    """Davlat nomini normallashtiradi."""
    cleaned = " ".join(raw.strip().split())
    key = cleaned.lower()
    return COUNTRY_ALIASES.get(key, cleaned.title())


def _extract_country(location_clean: str) -> str:
    """
    Turli formatlardan davlat nomini ajratadi:
      - "İstanbul (Türkiye)"   → "Türkiye"
      - "São Paulo (Brasil)"   → "Brazil"
      - "São Paulo, Brasil"    → "Brazil"
      - "South Africa"         → "South Africa"
    """
    # 1. Qavs ichidagi oxirgi qism: "City (Country)"
    m = re.search(r"\(([^)]+)\)\s*$", location_clean)
    if m:
        return _normalize_country(m.group(1))

    # 2. Verguldan keyingi qism: "City, Country"
    if "," in location_clean:
        after_comma = location_clean.rsplit(",", 1)[-1].strip()
        return _normalize_country(after_comma)

    # 3. To'g'ridan davlat nomi
    return _normalize_country(location_clean)


def _parse_status(status_cell: str) -> str:
    """
    Status matnini inglizcha va turkcha variantlardan aniqlaydi.

    Inglizcha: ACTIVE, SUSPENDED, WITHDRAWN
    Turkcha:   AKTİF, ASKIDA, İPTAL
    """
    upper = status_cell.upper()

    if any(x in upper for x in ["WITHDRAWN", "İPTAL", "IPTAL"]):
        return "withdrawn"
    elif any(x in upper for x in ["SUSPENDED", "ASKIDA"]):
        return "suspended"
    else:
        return "active"


def fetch_hak_directory() -> dict[str, list[dict]]:
    """
    HAK akkreditatsiya ro'yxati sahifasini yuklab olib,
    har bir davlat uchun sertifikat ma'lumotlarini qaytaradi.
    """
    log.info("🌐  HAK ro'yxati yuklanmoqda: %s", HAK_LIST_URL)
    try:
        r = requests.get(HAK_LIST_URL, headers=HEADERS, timeout=30)
        r.raise_for_status()
        r.encoding = r.apparent_encoding
    except Exception as e:
        log.error("❌  HAK sahifasi yuklanmadi: %s", e)
        return {}

    soup = BeautifulSoup(r.text, "lxml")
    result: dict[str, list[dict]] = {}

    tables = soup.find_all("table")
    main_table = None
    for tbl in tables:
        header_text = tbl.get_text(" ")
        if "HCAB Name" in header_text and "Location" in header_text:
            main_table = tbl
            break

    if not main_table:
        log.error("❌  Asosiy jadval topilmadi!")
        return {}

    rows = main_table.find_all("tr")
    log.info("   Jami %d ta qator topildi", len(rows))

    for row in rows[1:]:  # sarlavhani o'tkazib yuboramiz
        cells = row.find_all(["td", "th"])
        if len(cells) < 6:
            continue

        # Ustunlar tartibi:
        # 0: Logo | 1: HCAB Name + link | 2: Location | 3: Date of Issue
        # 4: Expiration Date | 5: Status/No | 6: Scope PDF | 7: Scope HTML

        # ── Tashkilot nomi va veb-sayti ──────────────────────────
        name_cell = cells[1]
        org_name  = name_cell.get_text(" ", strip=True).strip('"').strip("'")
        org_link  = ""
        a_tag = name_cell.find("a")
        if a_tag and a_tag.get("href"):
            org_link = a_tag["href"].strip()

        # ── Manzil / Davlat ──────────────────────────────────────
        location_raw   = cells[2].get_text(" ", strip=True)
        location_clean = " ".join(location_raw.split())

        # ✅ Endi qavs, vergul va to'g'ridan formatlarni qo'llab-quvvatlaydi
        country = _extract_country(location_clean)

        # ── Sanalar ──────────────────────────────────────────────
        initial_date = cells[3].get_text(" ", strip=True) if len(cells) > 3 else ""
        expiry_date  = cells[4].get_text(" ", strip=True) if len(cells) > 4 else ""

        # ── Status va akkreditatsiya raqami ──────────────────────
        status_text = cells[5].get_text(" ", strip=True) if len(cells) > 5 else ""
        acc_match   = re.search(r"(\d{4}-\d+)", status_text)
        acc_number  = acc_match.group(1) if acc_match else None

        status = _parse_status(status_text)

        # ── Scope URL lar ─────────────────────────────────────────
        scope_pdf_url  = ""
        scope_html_url = ""

        if len(cells) > 6:
            pdf_a = cells[6].find("a")
            if pdf_a and pdf_a.get("href"):
                scope_pdf_url = pdf_a["href"].strip()

        if len(cells) > 7:
            html_a = cells[7].find("a")
            if html_a and html_a.get("href"):
                scope_html_url = html_a["href"].strip()

        if not acc_number:
            log.debug("   ⏩  Akkreditatsiya raqami yo'q: %s", org_name)
            continue

        entry = {
            "accreditation_number": acc_number,
            "organization_name":    org_name,
            "org_website":          org_link,
            "location":             location_clean,
            "initial_date":         initial_date,
            "expiry_date":          expiry_date,
            "status":               status,
            "scope_pdf_url":        scope_pdf_url,
            "scope_html_url":       scope_html_url,
        }

        result.setdefault(country, []).append(entry)
        log.debug("   ✅  [%s] %s — %s (status: %s)", country, acc_number, org_name, status)

    countries = sorted(result.keys())
    total     = sum(len(v) for v in result.values())
    log.info("✅  %d ta davlat, jami %d ta sertifikat topildi", len(countries), total)
    log.info("   Davlatlar: %s", ", ".join(countries))

    return result

