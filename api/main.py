from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from api.routes import certificates, countries, search

app = FastAPI(
    title="Halal Sertifikatlar API",
    description="""
## 🕌 Halal Sertifikatlar API

HAK (Halal Akkreditatsiya Kurumu) ma'lumotlari asosida qurilgan API.

### Endpointlar:
- **Certificates** — Sertifikatlar ro'yxati, filtr va batafsil ma'lumot
- **Countries** — Davlatlar statistikasi
- **Search** — Erkin qidiruv
    """,
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(certificates.router, prefix="/api")
app.include_router(countries.router,    prefix="/api")
app.include_router(search.router,       prefix="/api")


@app.get("/api", tags=["Root"])
def root():
    return {
        "message": "🕌 Halal Sertifikatlar API",
        "version": "1.0.0",
        "docs": "/docs",
        "endpoints": {
            "certificates":       "/api/certificates",
            "certificate_by_acc": "/api/certificates/{acc_number}",
            "certificate_by_id":  "/api/certificates/id/{id}",
            "expiring":           "/api/certificates/expiring?days=30",
            "countries":          "/api/countries",
            "country_stats":      "/api/countries/{country}",
            "summary":            "/api/countries/summary",
            "search":             "/api/search?q=...",
        },
    }

# ← StaticFiles ENG OXIRIDA bo'lishi SHART
# Aks holda "/" root endpointni yutib yuboradi
app.mount("/", StaticFiles(directory="static", html=True), name="static")

