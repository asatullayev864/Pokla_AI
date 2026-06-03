from pydantic import BaseModel
from typing import Optional
from datetime import datetime


class ScopeItem(BaseModel):
    id: int
    certificate_id: int
    cluster: Optional[str]
    category_code: Optional[str]
    category_name: Optional[str]
    subcategory_code: Optional[str]
    subcategory_name: Optional[str]
    activities: Optional[str]

    class Config:
        from_attributes = True


class CertificateBase(BaseModel):
    accreditation_number: str
    country: str
    organization_name: Optional[str]
    address: Optional[str]
    standard: Optional[str]
    initial_date: Optional[str]
    expiry_date: Optional[str]
    status: Optional[str]
    scope_url: Optional[str]
    source_url: Optional[str]


class CertificateResponse(CertificateBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]
    scope_items: list[ScopeItem] = []

    class Config:
        from_attributes = True


class CertificateListResponse(CertificateBase):
    id: int
    created_at: Optional[datetime]
    updated_at: Optional[datetime]

    class Config:
        from_attributes = True


class CountryStats(BaseModel):
    country: str
    total_certificates: int
    active_certificates: int
    withdrawn_certificates: int
    suspended_certificates: int
    first_cert_date: Optional[str]
    latest_cert_date: Optional[str]
    updated_at: Optional[datetime]


class SummaryStats(BaseModel):
    total_countries: int
    total_certificates: int
    active_certificates: int
    withdrawn_certificates: int
    suspended_certificates: int


class PaginatedResponse(BaseModel):
    total: int
    page: int
    page_size: int
    pages: int
    data: list[CertificateListResponse]

