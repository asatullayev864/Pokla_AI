# test_country.py

from crawler.hak_directory import _extract_country

test_cases = [
    # (kiritma,               kutilgan natija)
    ("İstanbul (Türkiye)",    "Türkiye"),
    ("São Paulo (Brasil)",    "Brazil"),
    ("São Paulo, Brasil",     "Brazil"),
    ("Brazil",                "Brazil"),
    ("Brasil",                "Brazil"),
    ("South Africa",          "South Africa"),
    ("Ankara (Türkiye)",      "Türkiye"),
    ("Moscow (Russia)",       "Russia"),
    ("Dubai (UAE)",           "United Arab Emirates"),
    ("Tashkent (Uzbekistan)", "Uzbekistan"),
    ("Seoul (South Korea)",   "South Korea"),
]

print(f"{'Kiritma':<30} {'Kutilgan':<25} {'Natija':<25} {'✅/❌'}")
print("-" * 90)

passed = 0
for location, expected in test_cases:
    result = _extract_country(location)
    ok = result == expected
    if ok:
        passed += 1
    icon = "✅" if ok else "❌"
    print(f"{location:<30} {expected:<25} {result:<25} {icon}")

print("-" * 90)
print(f"Natija: {passed}/{len(test_cases)} ta to'g'ri")
