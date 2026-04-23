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
                "evidence": [],
                "submissions": [],
                "latest_dashboard": {},
                "latest_report": {},
                "library": [],
                "updated_at": self.utc_now_iso(),
            }
        record = companies[company_id]
        record.setdefault("profile", {})
        record.setdefault("onboarding", {})
        record.setdefault("plan", {})
        record.setdefault("uploads", [])
        record.setdefault("extractions", [])
        record.setdefault("monthly_updates", [])
        record.setdefault("evidence", [])
        record.setdefault("submissions", [])
        record.setdefault("latest_dashboard", {})
        record.setdefault("latest_report", {})
        record.setdefault("library", [])
        return record

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

    def save_evidence_file(
        self,
        company_id: str,
        evidence_payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record.setdefault("evidence", []).append(evidence_payload)
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(evidence_payload)

    def get_evidence_files(self, company_id: str) -> list[dict[str, Any]]:
        data = self._load()
        record = data.get("companies", {}).get(company_id)
        if not record:
            return []
        return deepcopy(record.get("evidence", []))

    def get_evidence_file(self, company_id: str, file_id: str) -> dict[str, Any] | None:
        evidence = self.get_evidence_files(company_id)
        for item in evidence:
            if item.get("file_id") == file_id:
                return item
        return None

    def delete_evidence_file(
        self,
        company_id: str,
        file_id: str,
    ) -> dict[str, Any] | None:
        data = self._load()
        record = data.get("companies", {}).get(company_id)
        if not record:
            return None

        evidence = record.get("evidence", [])
        for index, item in enumerate(evidence):
            if item.get("file_id") == file_id:
                removed = evidence.pop(index)
                record["updated_at"] = self.utc_now_iso()
                self._save(data)
                return deepcopy(removed)

        return None

    def save_submission(
        self,
        company_id: str,
        submission_payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record.setdefault("submissions", []).append(submission_payload)
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(submission_payload)

    def get_latest_submission(self, company_id: str) -> dict[str, Any] | None:
        data = self._load()
        record = data.get("companies", {}).get(company_id)
        if not record:
            return None
        submissions = record.get("submissions", [])
        if not submissions:
            return None
        return deepcopy(submissions[-1])

    def save_latest_dashboard(
        self,
        company_id: str,
        dashboard_payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record["latest_dashboard"] = dashboard_payload
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(dashboard_payload)

    def get_latest_dashboard(self, company_id: str) -> dict[str, Any] | None:
        data = self._load()
        record = data.get("companies", {}).get(company_id)
        if not record:
            return None
        dashboard = record.get("latest_dashboard")
        if not dashboard:
            return None
        return deepcopy(dashboard)

    def save_latest_report(
        self,
        company_id: str,
        report_payload: dict[str, Any],
    ) -> dict[str, Any]:
        data = self._load()
        company_record = self._ensure_company_record(data, company_id)
        company_record["latest_report"] = report_payload
        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(report_payload)

    def get_latest_report(self, company_id: str) -> dict[str, Any] | None:
        data = self._load()
        record = data.get("companies", {}).get(company_id)
        if not record:
            return None
        report = record.get("latest_report")
        if not report:
            return None
        return deepcopy(report)

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

    def reset_reporting_artifacts(self, company_id: str) -> dict[str, Any] | None:
        data = self._load()
        company_record = data.get("companies", {}).get(company_id)
        if not company_record:
            return None

        company_record["uploads"] = []
        company_record["extractions"] = []
        company_record["monthly_updates"] = []
        company_record["submissions"] = []
        company_record["latest_dashboard"] = {}
        company_record["latest_report"] = {}

        plan = company_record.get("plan")
        if isinstance(plan, dict) and plan:
            plan["kpis"] = []
            plan["ready_for_pdf"] = False

        library_entries = company_record.get("library", [])
        if isinstance(library_entries, list):
            company_record["library"] = [
                item
                for item in library_entries
                if item.get("entry_type") not in {"upload_extraction", "monthly_update"}
            ]

        company_record["updated_at"] = self.utc_now_iso()
        self._save(data)
        return deepcopy(company_record)
