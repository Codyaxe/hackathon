from __future__ import annotations

import json
from copy import deepcopy
from datetime import datetime, timezone
from pathlib import Path
from typing import Any
from uuid import uuid4


class ESGRepository:
    """File-backed repository for SME ESG workflow data."""

    def __init__(self, storage_path: Path):
        self.storage_path = storage_path
        self._ensure_store()

    def _default_document(self) -> dict[str, Any]:
        return {"companies": {}}

    def _ensure_store(self) -> None:
        self.storage_path.parent.mkdir(parents=True, exist_ok=True)
        if not self.storage_path.exists():
            self.storage_path.write_text(
                json.dumps(self._default_document(), indent=2), encoding="utf-8"
            )

    def _load(self) -> dict[str, Any]:
        self._ensure_store()
        try:
            raw = self.storage_path.read_text(encoding="utf-8").strip()
            if not raw:
                return self._default_document()
            data = json.loads(raw)
            if "companies" not in data:
                data["companies"] = {}
            return data
        except (json.JSONDecodeError, OSError):
            return self._default_document()

    def _save(self, data: dict[str, Any]) -> None:
        self.storage_path.write_text(json.dumps(data, indent=2), encoding="utf-8")

    def _ensure_company_record(
        self, data: dict[str, Any], company_id: str
    ) -> dict[str, Any]:
        companies = data.setdefault("companies", {})
        if company_id not in companies:
            companies[company_id] = {
                "profile": {},
                "onboarding": {},
                "plan": {},
                "uploads": [],
                "extractions": [],
                "monthly_updates": [],
                "library": [],
                "updated_at": self.utc_now_iso(),
            }
        return companies[company_id]

    @staticmethod
    def utc_now_iso() -> str:
        return datetime.now(timezone.utc).isoformat()

    def get_company_data(self, company_id: str) -> dict[str, Any] | None:
        data = self._load()
        record = data.get("companies", {}).get(company_id)
        if record is None:
            return None
        return deepcopy(record)

    def save_profile(self, company_id: str, profile: dict[str, Any]) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record["profile"] = profile
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(company_record)

    def save_onboarding(
        self, company_id: str, onboarding: dict[str, Any]
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record["onboarding"] = onboarding
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(company_record)

    def save_plan(self, company_id: str, plan: dict[str, Any]) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record["plan"] = plan
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(company_record)

    def save_upload_batch(
        self,
        company_id: str,
        upload_records: list[dict[str, Any]],
        extraction_payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record.setdefault("uploads", []).extend(upload_records)
        company_record.setdefault("extractions", []).append(extraction_payload)
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(company_record)

    def save_monthly_update(
        self, company_id: str, update_payload: dict[str, Any]
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record.setdefault("monthly_updates", []).append(update_payload)
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(company_record)

    def append_library_entry(
        self,
        company_id: str,
        entry_type: str,
        payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        entry = {
            "entry_id": str(uuid4()),
            "entry_type": entry_type,
            "created_at": self.utc_now_iso(),
            "payload": payload,
        }
        company_record.setdefault("library", []).append(entry)
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return entry

    def get_library_entries(
        self, company_id: str, limit: int = 50
    ) -> list[dict[str, Any]]:
        data = self._load()
        record = data.get("companies", {}).get(company_id)
        if not record:
            return []
        entries = list(record.get("library", []))
        entries.reverse()
        return entries[:limit]
