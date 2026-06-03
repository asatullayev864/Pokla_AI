#!/usr/bin/env python3
import logging
import sys
import os
from datetime import datetime

sys.path.insert(0, os.path.dirname(__file__))

from config import BASE_URL
from database.db import init_db, get_connection
from crawler.scraper import run

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s  %(levelname)-8s  %(message)s",
    datefmt="%H:%M:%S",
)
log = logging.getLogger(__name__)


def get_current_accreditation_numbers() -> set:
    conn = get_connection()
    cur = conn.cursor()
    cur.execute("SELECT accreditation_number FROM certificates")
    rows = cur.fetchall()
    cur.close()
    conn.close()
    return {r[0] for r in rows}


def check_and_update():
    log.info("=" * 55)
    log.info("🔍  Tekshirish boshlandi: %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    log.info("=" * 55)

    before = get_current_accreditation_numbers()
    log.info("📋  Avvalgi sertifikatlar soni: %d", len(before))

    init_db()
    run(BASE_URL)

    after = get_current_accreditation_numbers()
    log.info("📋  Yangi sertifikatlar soni: %d", len(after))

    added   = after - before
    removed = before - after

    if added:
        log.info("✅  YANGI QOSHILDI (%d ta):", len(added))
        for acc in added:
            log.info("    ➕  %s", acc)
    else:
        log.info("ℹ️   Yangi sertifikat yo'q")

    if removed:
        log.info("⚠️   O'CHIRILGAN (%d ta):", len(removed))
        for acc in removed:
            log.info("    ➖  %s", acc)

    if not added and not removed:
        log.info("✅  O'zgarish yo'q")

    log.info("=" * 55)
    log.info("✅  Tekshirish tugadi: %s", datetime.now().strftime("%Y-%m-%d %H:%M"))
    log.info("=" * 55)


if __name__ == "__main__":
    check_and_update()