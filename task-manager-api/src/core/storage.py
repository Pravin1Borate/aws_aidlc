import json
import os
from pathlib import Path


class JsonFileStorage:
    def __init__(self, file_path: str) -> None:
        self._path = Path(file_path)
        self._path.parent.mkdir(parents=True, exist_ok=True)

    def read_all(self) -> list[dict]:
        if not self._path.exists():
            return []
        return json.loads(self._path.read_text(encoding="utf-8"))

    def write_all(self, records: list[dict]) -> None:
        tmp = self._path.with_suffix(".tmp")
        tmp.write_text(json.dumps(records, indent=2, default=str), encoding="utf-8")
        os.replace(tmp, self._path)

    def find_by_id(self, record_id: str) -> dict | None:
        for record in self.read_all():
            if record.get("id") == record_id:
                return record
        return None

    def upsert(self, record: dict) -> dict:
        records = self.read_all()
        for i, r in enumerate(records):
            if r.get("id") == record.get("id"):
                records[i] = record
                self.write_all(records)
                return record
        records.append(record)
        self.write_all(records)
        return record

    def delete_by_id(self, record_id: str) -> bool:
        records = self.read_all()
        filtered = [r for r in records if r.get("id") != record_id]
        if len(filtered) == len(records):
            return False
        self.write_all(filtered)
        return True
