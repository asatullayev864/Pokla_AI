import re
import logging
from bs4 import BeautifulSoup

log = logging.getLogger(__name__)


def parse_certificate(html: str, source_url: str) -> dict:
    soup = BeautifulSoup(html, "lxml")
    text = soup.get_text("\n", strip=True)
    data = {"source_url": source_url}

    m = re.search(r"(?:Halal Accreditation Number|Helal Akreditasyon Numaras[ıi])\s*\n\s*(\d{4}-\d+)", text, re.I)
    data["accreditation_number"] = m.group(1).strip() if m else None
    log.info("   Raqam: %s", data["accreditation_number"])

    h3 = soup.find("h3")
    if h3:
        data["organization_name"] = h3.get_text(strip=True).replace('"', '').replace("'", '').strip()
    else:
        m = re.search(r"Halal Conformity Assessment Body\s*\n\s*(.+)", text, re.I)
        data["organization_name"] = m.group(1).strip().strip('"') if m else None
    log.info("   Tashkilot: %s", data["organization_name"])

    m = re.search(r"Address\s*:\s*(.+?)(?:\n|$)", text, re.I)
    if not m:
        m = re.search(r"Adres\s*:\s*(.+?)(?:\n|$)", text, re.I)
    data["address"] = m.group(1).strip() if m else None

    m = re.search(r"(OIC/SMIIC\s*\d+:\d+)", text)
    data["standard"] = m.group(1).strip() if m else None

    m = re.search(r"(?:Initial Halal Accreditation Date|[İI]lk Helal Akreditasyon Tarihi)\s*\n\s*(\d{2}\.\d{2}\.\d{4})", text, re.I)
    data["initial_date"] = m.group(1) if m else None

    m = re.search(r"(?:Expiry Date|Helal Akreditasyon Biti[sş] Tarihi)\s*\n\s*(\d{2}\.\d{2}\.\d{4})", text, re.I)
    data["expiry_date"] = m.group(1) if m else None

    data["scope_items"] = _parse_scope_table(soup)
    return data


def _parse_scope_table(soup: BeautifulSoup) -> list[dict]:
    items = []
    tables = soup.find_all("table")

    for table in tables:
        rows = table.find_all("tr")
        if not rows:
            continue
        if "Cluster" not in rows[0].get_text(" "):
            continue

        current_cluster  = ""
        current_cat_code = ""
        current_cat_name = ""

        for row in rows[1:]:
            cells = [td.get_text(" ", strip=True) for td in row.find_all(["td", "th"])]
            if not any(cells):
                continue

            if len(cells) >= 6:
                if cells[0]: current_cluster  = cells[0]
                if cells[1]: current_cat_code = cells[1]
                if cells[2]: current_cat_name = cells[2]
                subcat_code = cells[3]
                subcat_name = cells[4]
                activities  = cells[5]
            elif len(cells) == 4:
                subcat_code = cells[0]
                subcat_name = cells[1]
                activities  = cells[3] if cells[3] else cells[2]
            elif len(cells) == 3:
                subcat_code = cells[0]
                subcat_name = cells[1]
                activities  = cells[2]
            elif len(cells) == 2:
                subcat_code = cells[0]
                subcat_name = ""
                activities  = cells[1]
            else:
                continue

            if activities and subcat_code:
                items.append({
                    "cluster":          current_cluster,
                    "category_code":    current_cat_code,
                    "category_name":    current_cat_name,
                    "subcategory_code": subcat_code,
                    "subcategory_name": subcat_name,
                    "activities":       activities,
                })

    log.info("   Scope: %d ta element topildi", len(items))
    return items

